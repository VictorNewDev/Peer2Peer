def build_message(msg_type, data):
    return {"type": msg_type, "data": data}

def parse_message(msg):
    return msg.get("type"), msg.get("data")