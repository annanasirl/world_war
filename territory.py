class Territory():
    def __init__(self, name, owner, units_produced, units_stored):
        self.name = name;
        self.owner = owner;
        self.units_produced = units_produced;
        self.units_stored = units_stored;
        self.neighbors = [];

    def produce_units(self):
        if(self.owner != None):
            self.units_stored += self.units_produced

    def add_units(self, new_units):
        self.units_stored += new_units

    def add_neighbor(self, neighbor):
        self.neighbors.append(neighbor)

    def get_neighbors(self):
        return self.neighbors

    def get_owner(self):
        return self.owner

    def get_units_stored(self):
        return self.units_stored

    def get_units_produced(self):
        return self.units_produced

    def get_name(self):
        return self.name