"""ASGI application."""

from __future__ import annotations

import json
from http import HTTPStatus

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from oh_my_gtm.config import AppSettings, get_settings
from oh_my_gtm.database import create_session_factory, init_db
from oh_my_gtm.models import Workspace
from oh_my_gtm.orchestration.workflow import WorkflowEngine, describe_workflow_run
from oh_my_gtm.schemas import CSVSignalIngestionRequest, ContextPatchRequest, GTMContextInput, LinkedInExecuteRequest, LinkedInPrepareRequest, UrlSignalInput, VisibleCaptureIngestionRequest, WorkspaceCreateRequest, WorkspaceResponse
from oh_my_gtm.services.browser_executor import execute_linkedin_plan
from oh_my_gtm.services.context import merge_context, normalize_context
from oh_my_gtm.services.linkedin_agent import plan_from_request
from oh_my_gtm.services.signal_inbox import ingest_csv_signals, ingest_url_signals, ingest_visible_capture


def _openapi_spec() -> dict:
    return {
        "openapi": "3.1.0",
        "info": {"title": "oh-my-gtm API", "version": "0.1.0"},
        "paths": {
            "/api/workspaces": {"post": {"summary": "Create workspace"}},
            "/api/workspaces/{workspace_id}": {"get": {"summary": "Get workspace"}},
            "/api/workspaces/{workspace_id}/context": {"patch": {"summary": "Patch workspace context"}},
            "/api/workspaces/{workspace_id}/missing-fields": {"get": {"summary": "List missing fields"}},
            "/api/workspaces/{workspace_id}/signal-inbox/urls": {"post": {"summary": "Ingest URL signals"}},
            "/api/workspaces/{workspace_id}/signal-inbox/csv": {"post": {"summary": "Ingest CSV signals"}},
            "/api/workspaces/{workspace_id}/signal-inbox/capture": {"post": {"summary": "Ingest visible capture signals"}},
            "/api/workspaces/{workspace_id}/linkedin/prepare": {"post": {"summary": "Prepare a human-gated LinkedIn browser plan"}},
            "/api/workspaces/{workspace_id}/linkedin/execute": {"post": {"summary": "Execute a LinkedIn browser plan"}},
            "/api/workspaces/{workspace_id}/orchestrate": {"post": {"summary": "Run workflow"}},
            "/api/workflows/{workflow_id}": {"get": {"summary": "Get workflow status"}},
        },
    }


def _workspace_response(workspace: Workspace) -> WorkspaceResponse:
    return WorkspaceResponse(
        workspace_id=workspace.id,
        name=workspace.name,
        context=workspace.context_json,
        normalized_context=workspace.normalized_context_json,
        missing_fields=workspace.missing_fields_json,
        readiness_to_research=workspace.readiness_to_research,
        assumptions=workspace.assumption_summary_json,
    )


async def healthcheck(_: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


async def openapi(_: Request) -> JSONResponse:
    return JSONResponse(_openapi_spec())


async def create_workspace(request: Request) -> JSONResponse:
    payload = WorkspaceCreateRequest.model_validate(await request.json())
    session_factory = request.app.state.session_factory
    with session_factory() as session:
        workspace = Workspace(name=payload.workspace_name, context_json={}, normalized_context_json={}, missing_fields_json=["context_not_submitted"])
        session.add(workspace)
        session.commit()
        session.refresh(workspace)
        return JSONResponse(_workspace_response(workspace).model_dump(), status_code=HTTPStatus.CREATED)


async def patch_context(request: Request) -> JSONResponse:
    workspace_id = request.path_params["workspace_id"]
    payload = ContextPatchRequest.model_validate(await request.json())
    session_factory = request.app.state.session_factory
    with session_factory() as session:
        workspace = session.get(Workspace, workspace_id)
        if workspace is None:
            return JSONResponse({"detail": "workspace not found"}, status_code=HTTPStatus.NOT_FOUND)
        current = GTMContextInput.model_validate(workspace.context_json) if workspace.context_json else None
        merged = merge_context(current, payload.model_dump(exclude_none=True))
        normalized, assumptions, missing = normalize_context(merged)
        workspace.context_json = merged.model_dump()
        workspace.normalized_context_json = normalized.model_dump()
        workspace.missing_fields_json = missing
        workspace.readiness_to_research = normalized.readiness_to_research
        workspace.assumption_summary_json = [assumption.model_dump() for assumption in assumptions]
        session.add(workspace)
        session.commit()
        session.refresh(workspace)
        return JSONResponse(_workspace_response(workspace).model_dump())


async def get_workspace(request: Request) -> JSONResponse:
    workspace_id = request.path_params["workspace_id"]
    session_factory = request.app.state.session_factory
    with session_factory() as session:
        workspace = session.get(Workspace, workspace_id)
        if workspace is None:
            return JSONResponse({"detail": "workspace not found"}, status_code=HTTPStatus.NOT_FOUND)
        return JSONResponse(_workspace_response(workspace).model_dump())


async def get_missing_fields(request: Request) -> JSONResponse:
    workspace_id = request.path_params["workspace_id"]
    session_factory = request.app.state.session_factory
    with session_factory() as session:
        workspace = session.get(Workspace, workspace_id)
        if workspace is None:
            return JSONResponse({"detail": "workspace not found"}, status_code=HTTPStatus.NOT_FOUND)
        return JSONResponse({"workspace_id": workspace.id, "missing_fields": workspace.missing_fields_json})


async def prepare_linkedin_action(request: Request) -> JSONResponse:
    workspace_id = request.path_params["workspace_id"]
    payload = LinkedInPrepareRequest.model_validate(await request.json())
    session_factory = request.app.state.session_factory
    with session_factory() as session:
        workspace = session.get(Workspace, workspace_id)
        if workspace is None:
            return JSONResponse({"detail": "workspace not found"}, status_code=HTTPStatus.NOT_FOUND)
    plan = plan_from_request(payload)
    return JSONResponse(plan.model_dump())


async def execute_linkedin_action(request: Request) -> JSONResponse:
    workspace_id = request.path_params["workspace_id"]
    payload = LinkedInExecuteRequest.model_validate(await request.json())
    session_factory = request.app.state.session_factory
    with session_factory() as session:
        workspace = session.get(Workspace, workspace_id)
        if workspace is None:
            return JSONResponse({"detail": "workspace not found"}, status_code=HTTPStatus.NOT_FOUND)
    result = execute_linkedin_plan(payload.plan, request.app.state.settings, dry_run=payload.dry_run)
    return JSONResponse(result.model_dump())


async def ingest_signal_urls(request: Request) -> JSONResponse:
    workspace_id = request.path_params["workspace_id"]
    payload = [UrlSignalInput.model_validate(item) for item in await request.json()]
    session_factory = request.app.state.session_factory
    with session_factory() as session:
        workspace = session.get(Workspace, workspace_id)
        if workspace is None:
            return JSONResponse({"detail": "workspace not found"}, status_code=HTTPStatus.NOT_FOUND)
        result = ingest_url_signals(session, workspace_id, payload)
        session.commit()
    return JSONResponse(result.model_dump())


async def ingest_signal_csv(request: Request) -> JSONResponse:
    workspace_id = request.path_params["workspace_id"]
    payload = CSVSignalIngestionRequest.model_validate(await request.json())
    session_factory = request.app.state.session_factory
    with session_factory() as session:
        workspace = session.get(Workspace, workspace_id)
        if workspace is None:
            return JSONResponse({"detail": "workspace not found"}, status_code=HTTPStatus.NOT_FOUND)
        result = ingest_csv_signals(session, workspace_id, payload)
        session.commit()
    return JSONResponse(result.model_dump())


async def ingest_signal_capture(request: Request) -> JSONResponse:
    workspace_id = request.path_params["workspace_id"]
    payload = VisibleCaptureIngestionRequest.model_validate(await request.json())
    session_factory = request.app.state.session_factory
    with session_factory() as session:
        workspace = session.get(Workspace, workspace_id)
        if workspace is None:
            return JSONResponse({"detail": "workspace not found"}, status_code=HTTPStatus.NOT_FOUND)
        result = ingest_visible_capture(session, workspace_id, payload)
        session.commit()
    return JSONResponse(result.model_dump())


async def orchestrate(request: Request) -> JSONResponse:
    workspace_id = request.path_params["workspace_id"]
    session_factory = request.app.state.session_factory
    engine: WorkflowEngine = request.app.state.workflow_engine
    with session_factory() as session:
        workspace = session.get(Workspace, workspace_id)
        if workspace is None:
            return JSONResponse({"detail": "workspace not found"}, status_code=HTTPStatus.NOT_FOUND)
    result = engine.run(workspace_id, dry_run=True)
    return JSONResponse(json.loads(result.model_dump_json()))


async def get_workflow(request: Request) -> JSONResponse:
    workflow_id = request.path_params["workflow_id"]
    session_factory = request.app.state.session_factory
    with session_factory() as session:
        result = describe_workflow_run(session, workflow_id)
    return JSONResponse(json.loads(result.model_dump_json()))


def create_app(settings: AppSettings | None = None) -> Starlette:
    settings = settings or get_settings()
    session_factory = create_session_factory(settings)
    init_db(session_factory)
    app = Starlette(
        debug=settings.env == "local",
        routes=[
            Route("/health", healthcheck),
            Route("/openapi.json", openapi),
            Route("/api/workspaces", create_workspace, methods=["POST"]),
            Route("/api/workspaces/{workspace_id}", get_workspace, methods=["GET"]),
            Route("/api/workspaces/{workspace_id}/context", patch_context, methods=["PATCH"]),
            Route("/api/workspaces/{workspace_id}/missing-fields", get_missing_fields, methods=["GET"]),
            Route("/api/workspaces/{workspace_id}/signal-inbox/urls", ingest_signal_urls, methods=["POST"]),
            Route("/api/workspaces/{workspace_id}/signal-inbox/csv", ingest_signal_csv, methods=["POST"]),
            Route("/api/workspaces/{workspace_id}/signal-inbox/capture", ingest_signal_capture, methods=["POST"]),
            Route("/api/workspaces/{workspace_id}/linkedin/prepare", prepare_linkedin_action, methods=["POST"]),
            Route("/api/workspaces/{workspace_id}/linkedin/execute", execute_linkedin_action, methods=["POST"]),
            Route("/api/workspaces/{workspace_id}/orchestrate", orchestrate, methods=["POST"]),
            Route("/api/workflows/{workflow_id}", get_workflow, methods=["GET"]),
        ],
    )
    app.state.settings = settings
    app.state.session_factory = session_factory
    app.state.workflow_engine = WorkflowEngine(session_factory, settings)
    return app


app = create_app()
