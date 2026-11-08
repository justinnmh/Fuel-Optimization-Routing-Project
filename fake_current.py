import math


def add_fake_current(graph):
    """
    Add a smooth synthetic current field for testing.
    Values are not real Singapore current measurements.
    """
    for _, data in graph.nodes(data=True):
        lon = float(data["x"])
        lat = float(data["y"])

        # East/west current corridor around Singapore waters.
        east = (
            3.0 * math.exp(-((lat - 1.10) / 0.16) ** 2)
            - 2.0 * math.exp(-((lat - 1.48) / 0.18) ** 2)
        )

        # Smaller north/south variation.
        north = (
            0.7
            * math.sin((lon - 103.75) * 4.0)
            * math.exp(-((lat - 1.25) / 0.45) ** 2)
        )

        speed = math.hypot(east, north)
        direction = (math.degrees(math.atan2(east, north)) + 360) % 360

        data["current_east_knots"] = east
        data["current_north_knots"] = north
        data["current_speed_knots"] = speed
        data["current_direction_deg"] = direction
