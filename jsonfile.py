import json

def savejson(data):
    result = []
    for frame in data:
        frame_list = []
        for obj in frame:
            frame_list.append({
                "box": obj["box"].tolist(),  # convert numpy array → list
                "cx": float(obj["cx"]),
                "cy": float(obj["cy"]),
                "h": float(obj["h"])
            })
        result.append(frame_list)
        
    json_string = json.dumps(result)
    # print(json_string)
    return json_string

def load_json_sqlite(data):
    data = json.loads(data)

    # for frame in data:
    #     for obj in frame:
    #         obj["box"] = np.array(obj["box"], dtype=np.float32)
    #
    return data