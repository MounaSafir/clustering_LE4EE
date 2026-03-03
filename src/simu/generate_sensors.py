import random
import math

def generate_random(id, config, sensor):
    pos_x = random.randint(config.min_x, config.max_x)
    pos_y = random.randint(config.min_y, config.max_y)
    return sensor((pos_x, pos_y), id, config)


def generate_grid(id, config, sensor):
  
    if isinstance(id, str):
        idx = int(id.split("-")[-1])
    else:
        idx = id

    n = config.nb_sensors
    m = config.m
    nb_AN = int(m * n)

   
    if idx < nb_AN:
        cols = int(math.ceil(math.sqrt(nb_AN)))
        rows = int(math.ceil(nb_AN / cols))

        width = config.max_x - config.min_x
        height = config.max_y - config.min_y

        dx = width / (cols + 1)
        dy = height / (rows + 1)

        row = idx // cols
        col = idx % cols

        x = config.min_x + (col + 1) * dx
        y = config.min_y + (row + 1) * dy

        node = sensor((x, y), id, config)
        node.er = config.E_AN
        node.is_AN = True
        return node


    else:
        x = random.randint(config.min_x, config.max_x)
        y = random.randint(config.min_y, config.max_y)

        node = sensor((x, y), id, config)
        node.er = config.EI
        node.is_AN = False
        return node
