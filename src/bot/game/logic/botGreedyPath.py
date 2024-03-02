from game.logic.base import BaseLogic
from game.models import Board, GameObject
from random import randint

# GAME OBJECT TYPE:
# - Bot : BotGameObject 
# - Base : BaseGameObject 
# - Diamond : DiamondGameObject
# - Portal : TeleportGameObject
# - Diamond Button : DiamondButtonGameObject 

class BotGreedyPath(BaseLogic):
    def __init__(self):
        self.step_variation : bool = False
        self.step_ignore_portal : int = 0
        self.step_chase_enemy : int = 0
        self.current_distance_to_base : int = 0
        self.current_inventory_space : int = None

        # self.self.sorted_portals[0] is the portal closest to player, while [1] is further
        self.sorted_portals : list[GameObject] = []
        # self.self.distance_self_to_portals[0] is the distant to the portal closest to player, while [1] is further
        self.distance_self_to_portals : list[int] = []
        self.base : GameObject = None

        # Object Collection
        self.objects_base : list[GameObject] = []
        self.objects_portal : list[GameObject] = []
        self.objects_button : list[GameObject] = []
        self.red_diamonds : list[GameObject] = []
        self.blue_diamonds : list[GameObject] = []

    # ==================== GETTER ==================== #
    def getGameObjects(self, board: Board) -> None:
        self.objects_base = []
        self.objects_portal = []
        self.objects_button = []

        for game_object in board.game_objects:
            if game_object.type == "BaseGameObject":
                self.objects_base.append(game_object)
            elif game_object.type == "TeleportGameObject":
                self.objects_portal.append(game_object)
            elif game_object.type == "DiamondButtonGameObject":
                self.objects_button.append(game_object)
    def getDiamondsObject(self, board: Board) -> None:
        self.red_diamonds = []
        self.blue_diamonds = []

        for diamond in board.diamonds:
            if diamond.properties.points == 2:
                self.red_diamonds.append(diamond)
            else:
                self.blue_diamonds.append(diamond)

    def getBots(self, board: Board) -> list[GameObject]: return board.bots
    def getEnemyBots(self, this_bot: GameObject, board: Board) -> list[GameObject]: return [enemy for enemy in board.bots if enemy != this_bot]
    def getBases(self) -> list[GameObject]: return self.objects_base
    def getHomeBaseObject(self, this_bot: GameObject) -> GameObject: 
        for base in self.getBases():
            if base.properties.name == this_bot.properties.name:
                return base
        return None
    
    # ===== Get Diamond ===== #
    def getDiamonds(self, board: Board) -> list[GameObject]: return board.diamonds
    def getRedDiamonds(self) -> list[GameObject]: return self.red_diamonds
    def getBlueDiamonds(self) -> list[GameObject]: return self.blue_diamonds
    
    # ===== Get Portal ===== #
    def getPortals(self) -> list[GameObject]: return self.objects_portal
    def getSortedPortals(self, this_bot: GameObject) -> list[GameObject]: 
        # Sort portals based on distance to bot
        portals = self.getPortals()
        if portals:
            if self.distanceWithoutPortal(this_bot, portals[0]) < self.distanceWithoutPortal(this_bot, portals[1]):
                return portals[0], portals[1]
            else:
                return portals[1], portals[0]
        return None
    def getSortedPortalsDistance(self, this_bot: GameObject, board: Board) -> list[int]:
        if self.sorted_portals:
            return (self.distanceWithoutPortal(this_bot, self.sorted_portals[0]), self.distanceWithoutPortal(this_bot, self.sorted_portals[1]))
        else:
            return None
    
    # ===== Get Button ===== #
    def getDiamondButton(self) -> GameObject: return self.objects_button[0]

    # ===== Get Closest ===== #
    def getClosestRedDiamond(self, this_bot: GameObject, board: Board) -> GameObject:
        red_diamonds = self.getRedDiamonds()
        if not red_diamonds:
            return None
        return min(red_diamonds, key=lambda diamond: self.distance(this_bot, diamond, board))
    def getClosestBlueDiamond(self, this_bot: GameObject, board: Board) -> GameObject:
        blue_diamonds = self.getBlueDiamonds()
        if not blue_diamonds:
            return None
        return min(blue_diamonds, key=lambda diamond: self.distance(this_bot, diamond, board))
    def getClosestDiamond(self, this_bot: GameObject, board: Board) -> GameObject:
        diamonds = self.getDiamonds(board)
        if not diamonds:
            return None
        return min(diamonds, key=lambda diamond: self.distance(this_bot, diamond, board))
    def getClosestEnemy(self, this_bot: GameObject, board: Board) -> GameObject:
        enemies = self.getEnemyBots(this_bot, board)
        if not enemies:
            return None
        return min(enemies, key=lambda enemies: self.distance(this_bot, enemies, board))

    # ===== Get Inventory ===== #
    def getUsedInventorySpace(self, this_bot:GameObject) -> int: return this_bot.properties.diamonds
    def getEmptyInventorySpace(self, this_bot:GameObject) -> int: return this_bot.properties.inventory_size - this_bot.properties.diamonds
    
    # ===== Get Time ===== #
    # Time in second, each second is around a move
    def getTimeRemaining(self, this_bot:GameObject) -> int: return this_bot.properties.milliseconds_left // 1000

    # ==================== Checks ==================== #
    def isInventoryFull(self) -> bool: return self.current_inventory_space == 0
    def isInventoryEmpty(self, this_bot: GameObject) -> bool: return self.current_inventory_space == this_bot.properties.inventory_size

    # ==================== Distance ===================== #
    def distance(self, objectFrom: GameObject, objectTo: GameObject, board: Board) -> int: 
        # TODO Ignore Portal Distance addition
        if objectTo.type =="TeleportGameObject": return self.distanceWithoutPortal(objectFrom, objectTo)
        return min(self.distanceWithoutPortal(objectFrom, objectTo), self.distanceUsingPortal(objectFrom, objectTo, board))
    def distanceWithoutPortal(self, objectFrom: GameObject, objectTo: GameObject) -> int: return abs(objectFrom.position.y - objectTo.position.y) + abs(objectFrom.position.x - objectTo.position.x)
    def distanceUsingPortal(self, objectFrom: GameObject, objectTo: GameObject, board: Board) -> int:
        return self.distanceWithoutPortal(objectFrom, self.sorted_portals[0]) + self.distanceWithoutPortal(self.sorted_portals[1], objectTo)
    def distanceToClosestEnemy(self, this_bot: GameObject, board: Board) -> int: 
        enemy = self.getClosestEnemy(this_bot, board)
        if not enemy:
            return None
        return self.distance(this_bot, self.getClosestEnemy(this_bot, board), board)
    def distanceToBase(self, this_bot: GameObject, board: Board) -> int: return self.distance(this_bot, self.base, board)

    # ==================== Movement ==================== #
    def moveRight(self): return (1,0)
    def moveLeft(self): return (-1,0)
    def moveUp(self): return (0,1)
    def moveDown(self): return (0,-1)

    def moveToObjective(self, this_bot: GameObject, objective: GameObject, board: Board):
        x_diff:int = this_bot.position.x - objective.position.x
        y_diff:int = this_bot.position.y - objective.position.y

        # After Teleport
        if objective.type=="TeleportGameObject" and self.distance(this_bot, self.base, board) == 0:
            temp:int = randint(1,4)
            if temp == 1:
                return self.moveUp(this_bot, board)
            elif temp == 2:
                return self.moveDown(this_bot, board)
            elif temp == 3:
                return self.moveLeft(this_bot, board)
            else:
                return self.moveRight(this_bot, board)

        # Go To Portal if faster
        if objective.type!="TeleportGameObject" and self.distance(this_bot, self.base, board) > self.distanceUsingPortal(this_bot, self.base, board):
            print("PORTAL is closer!")
            return self.moveToObjective(this_bot, self.sorted_portals[0], board)

        if objective.type!="TeleportGameObject":
            # self.distance_self_to_portals[0] is the distance to the nearest portal
            if self.distance_self_to_portals[0] == 1:
                print("TRYING TO IGNORE PORTAL")
                x_portal_diff:int  = this_bot.position.x - self.sorted_portals[0].position.x
                y_portal_diff:int  = this_bot.position.y - self.sorted_portals[0].position.y

                # because portal is near make sure to avoid it
                if x_diff < 0 and x_portal_diff == -1 : 
                    self.step_ignore_portal = 1
                    if y_diff < 0 : return self.moveUp()
                    else : return self.moveDown()
                    
                elif x_diff > 0 and x_portal_diff == 1 : 
                    self.step_ignore_portal = 2
                    if y_diff < 0 : return self.moveUp()
                    else : return self.moveDown()
                    
                elif y_diff < 0 and y_portal_diff == -1 : 
                    self.step_ignore_portal = 3
                    if x_diff < 0 : return self.moveRight()
                    else : return self.moveLeft()

                elif y_diff > 0 and y_portal_diff == 1 : 
                    self.step_ignore_portal = 4
                    if x_diff < 0 : return self.moveRight()
                    else : return self.moveLeft()

        if self.step_ignore_portal == 1: self.step_ignore_portal = 0; print("IGNORE PORTAL Follow up"); return self.moveRight()
        elif self.step_ignore_portal == 2: self.step_ignore_portal = 0; print("IGNORE PORTAL Follow up"); return self.moveLeft()
        elif self.step_ignore_portal == 3: self.step_ignore_portal = 0; print("IGNORE PORTAL Follow up"); return self.moveUp()
        elif self.step_ignore_portal == 4: self.step_ignore_portal = 0; print("IGNORE PORTAL Follow up"); return self.moveDown()

        # Move directly toward objective
        if self.step_variation :
            self.step_variation = False
            if x_diff < 0 : return self.moveRight()
            elif x_diff > 0 : return self.moveLeft()
            elif y_diff < 0 : return self.moveUp()
            elif y_diff > 0 : return self.moveDown()
        else:
            self.step_variation = True
            if y_diff < 0 : return self.moveUp()
            elif y_diff > 0 : return self.moveDown()
            elif x_diff < 0 : return self.moveRight()
            elif x_diff > 0 : return self.moveLeft()

        return None
    
    # ===== Move to Object ===== #
    def moveToBase(self, this_bot: GameObject, board: Board):
        if self.distanceWithoutPortal(this_bot, self.base) > self.distanceUsingPortal(this_bot, self.base, board):
            return self.moveToObjective(this_bot, self.sorted_portals[0], board)
        return self.moveToObjective(this_bot, self.base, board)
    def moveToClosestEnemy(self, this_bot: GameObject, board: Board): return self.moveToObjective(this_bot, self.getClosestEnemy(this_bot, board), board)
    def moveToDiamondButton(self, this_bot: GameObject, board: Board): return self.moveToObjective(this_bot, self.getDiamondButton(), board)


    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    #
    # ==================== MAIN FUNCTION ==================== 
    # CURRENT ALGORITHM :
    #   1. If the time left is less than the distance to the base, then the bot will go to the base    
    #   2. If the Enemy is within one move, then the bot will attack it, unless the enemy is in it's base     
    #   3. If the bot's inventory is full, it will go to the base to deposit the diamonds  
    #   4. If the bot's inventory is half full but the base is near, deposit the diamonds    
    #   5. Go to the nearest diamond if inventory space is more than equal to 2   
    #   6. Go to the nearest blue diamond that is within 2 moves, if the bot's inventory is not full  
    #   7. If no diamonds are found, and the bot's inventory is not empty, then it will go to the base  
    #   8. If no diamonds are found and the bot's inventory is empty, then it will go to the diamond button  
    #
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    
    def next_move(self, this_bot: GameObject, board: Board):
    # BOT FUNCTION CALL BY ENGINE
        # Update dynamic var
        self.getGameObjects()
        self.getDiamondsObject()
        self.sorted_portals = self.getSortedPortals(this_bot)
        self.distance_self_to_portals = self.getSortedPortalsDistance(this_bot, board)
        self.current_distance_to_base = self.distanceToBase(this_bot, board)
        self.current_inventory_space = self.getEmptyInventorySpace(this_bot)
        
        # Update Static var
        if not self.base:
            self.base = self.getHomeBaseObject(this_bot)


    # 1. If the time left is less than the distance to the base, then the bot will go to the base    
        if not self.isInventoryEmpty(this_bot) and self.getTimeRemaining(this_bot) - 2 <= self.current_distance_to_base:
            # print("LOW TIME - GOING HOME")
            return self.moveToBase(this_bot, board)

    # 2. If the Enemy is within one move, then the bot will attack it, unless the enemy is in it's base    
        # TODO dont attack if enemy is it's base
        if self.distanceToClosestEnemy(this_bot, board) == 1 and self.step_chase_enemy <= 2 :
            # print("Attack Close Enemy.")
            self.step_chase_enemy += 1
            return self.moveToClosestEnemy(this_bot, board) 
        # logic to stop chasing attacking enemy after 3 tries
        elif self.step_chase_enemy == 4:
            self.step_chase_enemy = 0
        elif self.step_chase_enemy < 2:
            self.step_chase_enemy += 1

    # 3. If the bot's inventory is full, it will go to the base to deposit the diamonds  
        if self.isInventoryFull():  
            # print("Inventory Full.")
            return self.moveToBase(this_bot, board)

    # 4. If the bot's inventory is half full but the base is near, deposit the diamonds    
        if self.current_distance_to_base <= 2 and self.current_inventory_space <= (this_bot.properties.inventory_size // 2):
            return self.moveToBase(this_bot, board)

    # 5. Go to the nearest diamond if inventory space is more than equal to 2   
        closest_diamond = self.getClosestDiamond(this_bot, board)
        if closest_diamond and self.current_inventory_space >= 2:
            # print(f"Going to Diamond. Location : {closest_diamond.position}")
            return self.moveToObjective(this_bot, closest_diamond, board) 
            
    # 6. Go to the nearest blue diamond that is within 2 moves, if the bot's inventory is not full  
        if closest_diamond.properties.points == 2:
            closest_diamond = self.getClosestBlueDiamond(this_bot, board)
        if closest_diamond and not self.isInventoryFull() and closest_diamond.properties.points == 1 and self.distance(this_bot, closest_diamond, board) <= 2:
            # print(f"Going to Diamond. Location : {closest_diamond.position}")
            return self.moveToObjective(this_bot, closest_diamond, board) 

    # 7. If no diamonds are found, and the bot's inventory is not empty, then it will go to the base  
        if(not self.isInventoryEmpty(this_bot)):
            # print("Emptying Inventory.")
            return self.moveToBase(this_bot, board)
        
    # 8. If no diamonds are found and the bot's inventory is empty, then it will go to the diamond button  
        # print("Going to Diamond Button.")
        return self.moveToDiamondButton(this_bot, board)