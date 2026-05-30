# -*- coding: utf-8 -*-
"""设备相关 API routes。"""
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from ...lib.proxy import get_shared_proxy


async def list_devices(request: Request):
    room = request.query_params.get("room", "")
    refresh = request.query_params.get("refresh", "").lower() == "true"
    proxy = await get_shared_proxy()

    devices = await proxy.get_devices()
    if refresh:
        devices = await proxy.get_devices()

    homes = await proxy.get_homes()
    result = []
    for did, dev in devices.items():
        dev_room = ""
        for home in homes.values():
            if home.room_list:
                for rinfo in home.room_list.values():
                    if did in rinfo.dids:
                        dev_room = rinfo.room_name
                        break
        if room and room not in dev_room:
            continue
        result.append({
            "did": dev.did, "name": dev.name, "model": dev.model,
            "online": dev.online, "room": dev_room,
        })

    return JSONResponse({"total": len(result), "devices": result})


async def get_device(request: Request):
    did = request.path_params["did"]
    proxy = await get_shared_proxy()
    devices = await proxy.get_devices()
    dev = devices.get(did)
    if not dev:
        return JSONResponse({"error": f"未找到设备: {did}"}, status_code=404)

    spec = None
    if proxy._client and proxy._client.spec_parser:
        try:
            spec_raw = await proxy._client.spec_parser.parse_async(dev.model)
            if spec_raw:
                spec = {
                    "type": spec_raw.type,
                    "services": [
                        {
                            "iid": s.iid, "name": s.description,
                            "properties": [
                                {"iid": p.iid, "name": p.description, "format": p.format, "access": p.access}
                                for p in s.properties
                            ],
                            "actions": [
                                {"iid": a.iid, "name": a.description}
                                for a in s.actions
                            ],
                        }
                        for s in spec_raw.services
                    ],
                }
        except Exception:
            pass

    return JSONResponse({
        "did": dev.did, "name": dev.name, "model": dev.model,
        "online": dev.online, "spec": spec,
    })


async def device_on(request: Request):
    did = request.path_params["did"]
    proxy = await get_shared_proxy()
    result = await proxy.set_prop(did, siid=2, piid=1, value=True)
    return JSONResponse({"did": did, "action": "on", "result": result})


async def device_off(request: Request):
    did = request.path_params["did"]
    proxy = await get_shared_proxy()
    result = await proxy.set_prop(did, siid=2, piid=1, value=False)
    return JSONResponse({"did": did, "action": "off", "result": result})


async def device_prop(request: Request):
    did = request.path_params["did"]
    body = await request.json()
    siid, piid, value = body["siid"], body["piid"], body["value"]
    proxy = await get_shared_proxy()
    result = await proxy.set_prop(did, siid=siid, piid=piid, value=value)
    return JSONResponse({"did": did, "siid": siid, "piid": piid, "value": value, "result": result})


async def device_action(request: Request):
    did = request.path_params["did"]
    body = await request.json()
    siid, aiid = body["siid"], body["aiid"]
    in_list = body.get("in_list", [])
    proxy = await get_shared_proxy()
    result = await proxy.action(did, siid=siid, aiid=aiid, in_list=in_list)
    return JSONResponse({"did": did, "siid": siid, "aiid": aiid, "result": result})


routes = [
    Route("/devices", list_devices, methods=["GET"]),
    Route("/devices/{did}", get_device, methods=["GET"]),
    Route("/devices/{did}/on", device_on, methods=["POST"]),
    Route("/devices/{did}/off", device_off, methods=["POST"]),
    Route("/devices/{did}/prop", device_prop, methods=["POST"]),
    Route("/devices/{did}/action", device_action, methods=["POST"]),
]
