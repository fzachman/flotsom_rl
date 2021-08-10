from components.ai import HostileEnemy, BaseAI, Breather
from components import consumable, equippable
from components.equipment import Equipment
from components.fighter import Fighter
from components.inventory import Inventory
from components.level import Level
from components.lungs import Lungs, NoLungs
from components.lootable import Lootable
from components.light_source import LightSource
from components.powered import Powered
from entity import Entity, Actor, Item, Container

####################################################
#                      ACTORS                      #
####################################################
player = Actor(char='@',
               color=(255,255,255),
               name='Player',
               ai_cls=HostileEnemy,
               equipment=Equipment(),
               fighter=Fighter(hp=30,base_defense=1,base_power=2,base_accuracy=1),
               inventory=Inventory(capacity=26),
               level=Level(level_up_base=200),
               lungs=Lungs(max_o2=20,depletion_time=4),
               lootable=Lootable(),
               light_source=LightSource(radius=4))

crazed_crewmate = Actor(char='c',
                        color=(63,127,63),
                        name='Crazed Crewmate',
                        ai_cls=[Breather, HostileEnemy],
                        equipment=Equipment(),
                        fighter=Fighter(hp=6,base_defense=0,base_power=4,base_accuracy=0),
                        inventory=Inventory(capacity=0),
                        level=Level(xp_given=35),
                        lungs=Lungs(max_o2=10,depletion_time=4),
                        lootable=Lootable())

xeno_scuttler = Actor(char='s',
                      color=(0,127,0),
                      name='Xeno Scuttler',
                      ai_cls=[Breather, HostileEnemy],
                      equipment=Equipment(),
                      fighter=Fighter(hp=16,base_defense=1,base_power=5,base_accuracy=0),
                      inventory=Inventory(capacity=0),
                      level=Level(xp_given=100),
                      lungs=Lungs(max_o2=40,depletion_time=4),
                      lootable=Lootable())

####################################################
#                  CONSUMABLES                     #
####################################################
stimpack = Item(
  char='!',
  color=(127,0,255),
  name='StimPack',
  consumable=consumable.HealingConsumable(amount=8)
)

energy_cell = Item(
  char='=',
  color=(50,50,255),
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

####################################################
#                  EQUIPPABLES                     #
####################################################

knife = Item(char='/',
             color=(0,191,255),
             name='Knife',
             equippable=equippable.Knife()
             )

power_fist = Item(char='/',
             color=(0,191,255),
             name='Power Fist',
             equippable=equippable.PowerFist(),
             powered=Powered(10)
             )
popgun = Item(char=';',
              color=(0,191,255),
              name="Pop Gun",
              equippable=equippable.Gun(),
              powered=Powered(6))

spacer_suit = Item(char='[',
                  color = (139,69,19),
                  name='Basic Spacer Suit',
                  equippable=equippable.SpacersSuit())

armored_spacer_suit = Item(char='[',
                          color = (139,69,19),
                          name='Armored Spacer Suit',
                          equippable=equippable.ArmoredSpacersSuit())

shield_belt = Item(char='0',
                   color = (128,128,255),
                   name='Shield Belt',
                   equippable=equippable.ShieldBelt(),
                   powered=Powered(max_power=20, efficiency=2))

####################################################
#                  LIGHTS                          #
####################################################
light = Entity(char='*', color=(255,255,255), name='', light_source=LightSource(radius=4))


####################################################
#                  CONTAINERS                      #
####################################################
container_locker = Container(char='',
                             color=(128,128,128),
                             name='Locker',
                             lootable=Lootable())
