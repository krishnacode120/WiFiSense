from fastapi import APIRouter, Request, Query
from sqlalchemy import select
from app.models import ConnectionEvent, NetworkHistory, SignalHistory
from app.schemas import TrustCreate, TrustUpdate, Settings
from app.services.network_manager import public_trust

router = APIRouter(prefix="/api")


def manager(request):
    return request.app.state.manager


@router.get("/wifi/current")
def current(request: Request):
    return manager(request).status()


@router.get("/wifi/scan")
def scan(request: Request):
    m = manager(request)
    m.status()
    return m.scan()


@router.get("/wifi/trusted")
def trusted(request: Request):
    return [public_trust(n) for n in manager(request).trusted()]


@router.post("/wifi/trusted", status_code=201)
def add_trusted(payload: TrustCreate, request: Request):
    return manager(request).trust(payload)


@router.patch("/wifi/trusted/{identity}")
def update_trusted(identity: str, payload: TrustUpdate, request: Request):
    return manager(request).update_trust(identity, payload)


@router.delete("/wifi/trusted/{identity}")
def delete_trusted(identity: str, request: Request):
    manager(request).forget(identity)
    return {"ok": True}


@router.post("/wifi/connect/{identity}")
def connect(identity: str, request: Request):
    return manager(request).connect(identity)


@router.post("/wifi/disconnect")
def disconnect(request: Request):
    return manager(request).disconnect()


@router.post("/wifi/auto-connect/enable")
def enable(request: Request):
    m = manager(request)
    return m.save_settings(m.settings.model_copy(update={"auto_connect": True}))


@router.post("/wifi/auto-connect/disable")
def disable(request: Request):
    m = manager(request)
    return m.save_settings(m.settings.model_copy(update={"auto_connect": False}))


@router.get("/wifi/history")
def history(request: Request, limit: int = Query(100, ge=1, le=2000), offset: int = Query(0, ge=0)):
    m = manager(request)
    with m.sessions() as db:
        return list(db.scalars(select(ConnectionEvent).where(ConnectionEvent.mode == m.mode).order_by(ConnectionEvent.id.desc()).offset(offset).limit(limit)))


@router.get("/wifi/metrics")
def metrics(request: Request, limit: int = Query(500, ge=1, le=2000)):
    m = manager(request)
    with m.sessions() as db:
        connections = list(db.scalars(select(NetworkHistory).where(NetworkHistory.mode == m.mode).order_by(NetworkHistory.id.desc()).limit(limit)))
        signals = list(db.scalars(select(SignalHistory).where(SignalHistory.mode == m.mode).order_by(SignalHistory.id.desc()).limit(limit)))
        return {"connections": list(reversed(connections)), "signals": list(reversed(signals))}


@router.get("/settings")
def get_settings(request: Request):
    return manager(request).settings


@router.put("/settings")
def put_settings(payload: Settings, request: Request):
    return manager(request).save_settings(payload)


@router.get("/system/status")
def system(request: Request):
    m = manager(request)
    return {"mode": m.mode, "monitoring": bool(request.app.state.monitor and request.app.state.monitor.thread.is_alive()),
            "adapter": type(m.adapter).__name__, "error": m.last_error, "version": "1.0.0",
            "credential_storage": "OS keyring"}
