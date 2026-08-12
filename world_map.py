import territory as t

def add_as_neighbors(territory1, territory2):
    territory1.add_neighbor(territory2)
    territory2.add_neighbor(territory1)

def init_world():
    NorthAmerica = t.Territory("North America", "none", 6, 0)
    SouthAmerica = t.Territory("South America", "none", 5, 0)
    Europe = t.Territory("Europe", "none", 6, 0)
    NorthernAfrica = t.Territory("Northern Africa", "none", 4, 0)
    SouthernAfrica = t.Territory("Southern Africa", "none", 5, 0)
    WestAsia = t.Territory("West Asia", "none", 5, 0)
    EastAsia = t.Territory("East Asia", "none", 5, 0)
    Oceania = t.Territory("Oceania", "none", 4, 0)

    add_as_neighbors(NorthAmerica, SouthAmerica)
    add_as_neighbors(NorthAmerica, Europe)
    add_as_neighbors(NorthAmerica, EastAsia)
    add_as_neighbors(EastAsia, WestAsia)
    add_as_neighbors(EastAsia, Oceania)
    add_as_neighbors(Europe, WestAsia)
    add_as_neighbors(Europe, NorthernAfrica)
    add_as_neighbors(NorthernAfrica, WestAsia)
    add_as_neighbors(NorthernAfrica, SouthernAfrica)
    add_as_neighbors(Oceania, SouthernAfrica)
    add_as_neighbors(SouthAmerica, SouthernAfrica)

    territories = [NorthAmerica,SouthAmerica,Europe,NorthernAfrica,SouthernAfrica,WestAsia,EastAsia,Oceania]
    return territories