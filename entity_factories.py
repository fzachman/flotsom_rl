from components.ai import HostileEnemy, BaseAI
from components import consumable, equippable
from components.equipment import Equipment
from components.fighter import Fighter
from components.inventory import Inventory
from components.level import Level
from entity import Actor, Item

player = Actor(char='@',
               color=(255,255,255),
               name='Player',
               ai_cls=HostileEnemy,
               equipment=Equipment(),
               fighter=Fighter(hp=30,base_defense=1,base_power=2,base_accuracy=1),
               inventory=Inventory(capacity=26),
               level=Level(level_up_base=200))

crazed_crewmate = Actor(char='c',
                        color=(63,127,63),
                        name='Crazed Crewmate',
                        ai_cls=HostileEnemy,
                        equipment=Equipment(),
                        fighter=Fighter(hp=8,base_defense=0,base_power=4,base_accuracy=0),
                        inventory=Inventory(capacity=0),
                        level=Level(xp_given=35),)

xeno_scuttler = Actor(char='s',
                      color=(0,127,0),
                      name='Xeno Scuttler',
                      ai_cls=HostileEnemy,
                      equipment=Equipment(),
                      fighter=Fighter(hp=16,base_defense=1,base_power=5,base_accuracy=0),
                      inventory=Inventory(capacity=0),
                      level=Level(xp_given=100),)

stimpack = Item(
  char='!',
  color=(127,0,255),
  name='StimPack',
  consumable=consumable.HealingConsumable(amount=4)
)

energy_cell = Item(
  char='=',
  color=(150,150,255),
  name='Power Cell',
  consumable=consumable.EnergyConsumable(amount=10)
)

laser_drone = Item(
  char='~',
  color=(255,255,0),
  name='Laser Drone',
  consumable=consumable.LightningDamageConsumable(damage=20, maximum_range=5)
)

neural_scrambler = Item(
  char='~',
  color=(207,63,255),
  name='Neural Scrambler',
  consumable=consumable.ConfusionConsumable(number_of_turns=10)
)

grenade_fire = Item(
  char='~',
  color=(255,0,0),
  name='Explosive Grenade',
  consumable=consumable.FireballDamageConsumable(damage=12, radius=3)
)

knife = Item(char='/',
             color=(0,191,255),
             name='Knife',
             equippable=equippable.Knife()
             )

power_fist = Item(char='/',
             color=(0,191,255),
             name='Power Fist',
             equippable=equippable.PowerFist()
             )
popgun = Item(char=';',
              color=(0,191,255),
              name="Pop Gun",
              equippable=equippable.Gun())

spacer_suit = Item(char='[',
                  color = (139,69,19),
                  name='Basic Spacer Suit',
                  equippable=equippable.SpacersSuit())

armored_spacer_suit = Item(char='[',
                          color = (139,69,19),
                          name='Armored Spacer Suit',
                          equippable=equippable.ArmoredSpacersSuit())
