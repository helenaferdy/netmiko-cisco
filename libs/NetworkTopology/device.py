class Device:
    def __init__(self, source, target, weight):
        self.source = source
        self.target = target
        self.weight = weight

        self.neighbor = []

    def add_neighbor(self, new_neighbor):
        self.neighbor.append(new_neighbor)