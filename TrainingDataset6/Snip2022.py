def sync_large_receive(payload: LargeIn):
    return {"received": len(payload.items)}