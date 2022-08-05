from contextlib import nullcontext
import random
import math
from pyswip import Prolog
import sys

pl = Prolog()
pl.consult("TeamHelloKitty_agent.pl")


class Agent:
    def __init__(self, map, RelativeMap):
        self.grid = map
        self.relativeMap = RelativeMap
        self.x = 1
        self.y = 5
        self.direction = "north"
        self.sensorInformation = ["on", "off", "off", "off", "off", "off"]
        self.start_scream = 1
        self.origin = (1, 1)
        self.endGame = False

    def createAgent(self):
        self.x = 1
        self.y = 1
        self.direction = "north"
        self.origin = (1, 1)
        self.start_scream = 1
        self.sensorInformation = self.grid.getSensorInfo((self.x, self.y))
        self.sensorInformation[0] = 1
        bool(list(pl.query("reborn()")))
        bool(list(pl.query(f"reposition({self.sensorInformation})")))
        self.relativeMap.changeStartPos(0, 0)
        self.grid.createAgentOnMap(self.x, self.y, self.direction)

    def moveForward(self):
        bumpSensor = False
        print("Action performed: move forward")
        old_x = self.x
        old_y = self.y

        if self.direction == "north":
            self.y = self.y + 1
        elif self.direction == "south":
            self.y = self.y - 1
        elif self.direction == "west":
            self.x = self.x - 1
        elif self.direction == "east":
            self.x = self.x + 1

        if self.x <= 0 or self.y >= 6 or self.x >= 5 or self.y <= 0:
            self.x = old_x
            self.y = old_y
            bumpSensor = True
        if bumpSensor == False and (
            self.direction == "north" or self.direction == "south"
        ):
            self.relativeMap.addExtraRows(2, self.direction)
        if bumpSensor == False and (
            self.direction == "east" or self.direction == "west"
        ):
            self.relativeMap.addExtraColumns(2, self.direction)
        return bumpSensor

    def turnLeft(self):
        print("Action performed: turn left")
        if self.direction == "north":
            self.direction = "west"
        elif self.direction == "east":
            self.direction = "north"
        elif self.direction == "south":
            self.direction = "east"
        elif self.direction == "west":
            self.direction = "south"

    def turnRight(self):
        print("Action performed: turn right")
        if self.direction == "north":
            self.direction = "east"
        elif self.direction == "east":
            self.direction = "south"
        elif self.direction == "south":
            self.direction = "west"
        elif self.direction == "west":
            self.direction = "north"

    def pickUp(self):
        print("Action performed: pickup")
        if (self.x, self.y) == self.grid.utils.gold:
            self.grid.utils.gold = None  # remove coin from npc
            print("Picked up coin")
        else:
            print("No coin in this position")

    def shoot(self):
        screamSensor = False
        print("Action performed: shoot")
        forwardX = self.x
        forwardY = self.y

        if self.direction == "north":
            forwardY = forwardY + 1
        elif self.direction == "east":
            forwardX = forwardX + 1
        elif self.direction == "south":
            forwardY = forwardY - 1
        elif self.direction == "west":
            forwardX = forwardX - 1

        if bool(list(pl.query("hasarrow"))):
            if (forwardX, forwardY) == self.grid.utils.wumpus:
                screamSensor = True
                self.grid.utils.wumpus = None
                print("Successfully killed the Wumpus")
                self.relativeMap.heardScream()
            else:
                print("Did not kill Wumpus")
        else:
            print("No arrow to shoot")

        return screamSensor

    def move(self, action):
        bumpSensor = False
        screamSensor = False
        if action == "moveforward":
            bumpSensor = self.moveForward()
        elif action == "turnleft":
            self.turnLeft()
        elif action == "turnright":
            self.turnRight()
        elif action == "pickup":
            self.pickUp()
        elif action == "shoot":
            screamSensor = self.shoot()

        self.sensorInformation = self.grid.getSensorInfo(
            (self.x, self.y), bumpSensor, screamSensor
        )

        bool(list(pl.query(f"move({action},{(self.sensorInformation)})")))

        if self.sensorInformation[0] == 1:
            self.enteredConfundusPortal()
            self.sensorInformation = self.grid.getSensorInfo((self.x, self.y))
            self.sensorInformation[0] = 1
            bool(list(pl.query(f"reposition({(self.sensorInformation)})")))

        self.relativeMap.printRelativeMap(self.sensorInformation)

        self.checkGameover()

    def runStepbyStep(self):
        print(list(pl.query("explore(L)")))
        actions = list(pl.query("explore(L)"))[0]["L"]

        input("Enter to continue")
        for i in actions:
            a = str(i)
            self.move(a)

    def runThrough(self):
        actions = list(pl.query("explore(L)"))[0]["L"]
        for i in actions:
            a = str(i)
            self.move(a)

    def enteredConfundusPortal(self):
        print(
            "=========================Entered a Confundus Portal========================="
        )
        listofUtils = set()
        typeCoin = type(self.grid.utils.gold) is tuple

        if self.grid.utils.wumpus != None:
            listofUtils.add(self.grid.utils.wumpus)

        for i in range(len(self.grid.utils.confundus)):
            listofUtils.add(self.grid.utils.confundus[i])

        if typeCoin == False:
            for i in range(len(self.grid.utils.gold)):
                listofUtils.add(self.grid.utils.gold[i])
        else:
            listofUtils.add(self.grid.utils.gold)
        flag = False
        while flag == False:
            newX = random.randint(1, self.grid.columns - 2)
            newY = random.randint(1, self.grid.rows - 2)
            newPosition = (newX, newY)
            if newPosition not in listofUtils:
                flag = True
                print("New position of the agent on the absolute map is", newPosition)
                self.x = newX
                self.y = newY
                self.direction = "north"
                self.origin = (newX, newY)
                self.relativeMap.enteredConfundusPortal(0, 0)
                self.grid.clearelativeMap()
                self.grid.spawnUtils()
                self.grid.createAgentOnMap(self.x, self.y, self.direction)
                self.grid.printRelativeMap()

    def checkGameover(self):
        w = self.enterWumpusCell()
        o = self.returnToOrign()
        if w == True or o == True:
            print("=========================GAME OVER=========================")
            sys.exit()

    def returnToOrign(self):
        if self.grid.utils.gold == None and (self.x, self.y) == self.origin:
            print(
                "Congratulations! The coin was collected and the agent returned to origin."
            )
            return True
        return False

    def enterWumpusCell(self):
        if self.grid.utils.wumpus == None:
            return False
        if (self.x, self.y) == self.grid.utils.wumpus:
            print("Sorry! The agent entered the wumpus cell. GAME OVER")
            return True
        else:
            return False


class Utils:
    def __init__(self):
        self.wumpus = None
        self.gold = None
        self.confundus = [None, None, None]

    def intializationUtils(self):
        self.wumpus = (1, 3)
        self.gold = (2, 3)
        self.confundus = [(3, 1), (3, 3), (4, 4)]

    def spawnUtils(self, agent_X, agent_Y, rows, columns):
        co_ords = set()
        co_ords.add((agent_X, agent_Y))

        while len(co_ords) != 6:
            x = random.randint(1, columns - 2)
            y = random.randint(1, rows - 2)
            co_ords.add((x, y))
        co_ords.remove((agent_X, agent_Y))

        self.wumpus = co_ords.pop()
        self.gold = co_ords.pop()
        self.confundus[0] = co_ords.pop()
        self.confundus[1] = co_ords.pop()
        self.confundus[2] = co_ords.pop()

    def printUtilsPosition(self):
        print(f"Wumpus is at: {self.wumpus}", end=", ")
        print(f"Coin is at: {self.gold}", end=", ")
        print(f"Confundus Portal 1 is at: {self.confundus[0]}", end=", ")
        print(f"Confundus Portal 2 is at: {self.confundus[1]}", end=", ")
        print(f"Confundus Portal 3 is at: {self.confundus[2]}")


class AbsoluteMap:
    def __init__(self, n_rows, n_columns, n_cell):
        self.rows = n_rows
        self.columns = n_columns
        self.cell = n_cell
        self.grid = []
        self.utils = None
        self.agent = None

    def mapCreation(self):
        self.grid = []
        for i in range(self.rows):
            self.grid.append([])
            for j in range(self.columns):
                self.grid[i].append([])
                for k in range(self.cell):
                    if i == 0 or i == self.rows - 1 or j == 0 or j == self.columns - 1:
                        self.grid[i][j].append("#")
                    else:
                        if k == 3 or k == 5:
                            self.grid[i][j].append(" ")
                        elif k == 4:
                            self.grid[i][j].append("?")
                        else:
                            self.grid[i][j].append(".")

    def initialisation(self, utils, agent):
        self.utils = utils
        self.agent = agent

    def restartGame(self):
        self.agent.createAgent()
        self.utils.intializationUtils()
        self.spawnUtils()
        self.utils.printUtilsPosition()
        self.printRelativeMap()
        self.agent.relativeMap.printRelativeMap(self.agent.sensorInformation)

    def clearelativeMap(self):
        for i in range(1, self.rows - 1):
            for j in range(1, self.columns - 1):
                for k in range(self.cell):
                    self.grid[i][j][k] = "."
        for i in range(1, self.rows - 1):
            for j in range(1, self.columns - 1):
                self.grid[i][j][4] = "?"

    def putUtilOnGrid(self, npc_X, npc_Y, symbol):
        self.grid[npc_Y][npc_X][3] = "—"
        self.grid[npc_Y][npc_X][5] = "—"
        self.grid[npc_Y][npc_X][4] = symbol

    def spawnUtils(self):
        if self.utils.wumpus != None:
            self.putUtilOnGrid(self.utils.wumpus[0], self.utils.wumpus[1], "W")
        if self.utils.gold != None:
            self.putUtilOnGrid(self.utils.gold[0], self.utils.gold[1], "C")
        self.putUtilOnGrid(self.utils.confundus[0][0], self.utils.confundus[0][1], "O")
        self.putUtilOnGrid(self.utils.confundus[1][0], self.utils.confundus[1][1], "O")
        self.putUtilOnGrid(self.utils.confundus[2][0], self.utils.confundus[2][1], "O")

    def createAgentOnMap(self, x, y, direction):
        if direction == "north":
            self.grid[y][x][4] = "^"
        elif direction == "east":
            self.grid[y][x][4] = ">"
        elif direction == "south":
            self.grid[y][x][4] = "v"
        elif direction == "west":
            self.grid[y][x][4] = "<"
        self.grid[y][x][3] = "—"
        self.grid[y][x][5] = "—"

    def getSensorInfo(self, agentPos, bump=False, scream=False):
        up = (agentPos[0], agentPos[1] + 1)
        down = (agentPos[0], agentPos[1] - 1)
        left = (agentPos[0] - 1, agentPos[1])
        right = (agentPos[0] + 1, agentPos[1])
        sensors = ["off", "off", "off", "off", "off", "off"]
        if bump:
            sensors[4] = "on"
        if scream:
            sensors[5] = "on"
        if agentPos in self.utils.confundus:
            sensors[0] = "on"
        if agentPos == self.utils.gold:
            sensors[3] = "on"
        if (
            up == self.utils.wumpus
            or left == self.utils.wumpus
            or down == self.utils.wumpus
            or right == self.utils.wumpus
        ):
            sensors[1] = "on"
        if (
            up in self.utils.confundus
            or down in self.utils.confundus
            or right in self.utils.confundus
            or left in self.utils.confundus
        ):
            sensors[2] = "on"
        return sensors

    def printRelativeMap(self):
        innerCellColumn = self.cell // 3
        innerCellRow = self.cell // 3
        print()
        print("=================Absolute Map====================")
        print("-------------------------------------------------")
        for i in range(self.rows - 1, -1, -1):
            for j in range(innerCellRow):
                print("|", end="")
                for k in range(self.columns):
                    print(" ", end="")
                    for l in range(innerCellColumn):
                        print(self.grid[i][k][j * innerCellRow + l] + " ", end="")
                    print("|", end="")
                print()
            print("-------------------------------------------------")
        print()

    def printsensorInformation(self, sensorInformation):
        sensorNames = ["Confounded", "Stench", "Tingle", "Glitter", "Bump", "Scream"]
        sensorString = ""
        for i in range(len(sensorInformation)):
            if sensorInformation[i] == "on":
                sensorString = sensorString + sensorNames[i] + "—"
            else:
                sensorString = sensorString + sensorNames[i][0] + "—"

        print("Sensors: " + sensorString)


class RelativeMap(AbsoluteMap):
    def __init__(self, n_rows, n_columns, n_cell):
        self.rows = n_rows
        self.columns = n_columns
        self.cell = n_cell
        self.x = 0
        self.y = 0
        self.start_scream = 0
        self.local_X = 0
        self.local_Y = 0
        self.maximum_x = False
        self.maximum_y = False

    def printRelativeMap(self, sensorInformation):
        self.printsensorInformation(sensorInformation)
        print("Relative Map of the Agent:")
        x_mod = math.floor(self.columns / 2)
        start_X = self.x - x_mod
        y_mod = math.floor(self.rows / 2)
        start_Y = self.y + y_mod
        for _ in range(self.rows):
            self.getRowPrintout(start_X, start_Y, self.columns)
            print()
            start_Y = start_Y - 1
        print()

    def getNumberOfRows(self):
        return self.rows

    def getNumberOfColumns(self):
        return self.columns

    def setNumberOfRows(self, val):
        self.rows = val

    def setNumberOfColumns(self, val):
        self.columns = val

    def addExtraRows(self, value, direction):
        if self.maximum_y == True:
            return
        if direction == "north":
            self.local_Y = self.local_Y + 1
            if self.local_Y >= 4:
                self.maximum_y = True
            if self.local_Y <= 0 or self.local_Y > 4:
                return
        elif direction == "south":
            self.local_Y = self.local_Y - 1
            if self.local_Y <= -4:
                self.maximum_y = True
            if self.local_Y >= 0 or self.local_Y < -4:
                return
        self.rows = self.getNumberOfRows() + value

    def addExtraColumns(self, value, direction):
        if self.maximum_x == True:
            return
        if direction == "east":
            self.local_X = self.local_X + 1
            if self.local_X >= 3:
                self.maximum_x = True
            if self.local_X <= 0 or self.local_X > 3:
                return
        elif direction == "west":
            self.local_X = self.local_X - 1
            if self.local_X <= -3:
                self.maximum_x = True
            if self.local_X >= 0 or self.local_X < -3:
                return
        self.columns = self.getNumberOfColumns() + value

    def enteredConfundusPortal(self, newX, newY):
        self.changeStartPos(newX, newY)

    def changeStartPos(self, x, y):
        self.setNumberOfRows(3)
        self.setNumberOfColumns(3)
        self.x = x
        self.y = y
        self.local_X = 0
        self.local_Y = 0
        self.maximum_x = False
        self.maximum_y = False

    def getRowPrintout(self, x, y, n_rooms):
        print("| ", end="")

        for k in range(n_rooms):
            x1 = x + k
            if bool(list(pl.query(f"wall({x1}, {y})"))):
                print("# # #", end=" ")
                print("| ", end="")
                continue
            if bool(list(pl.query(f"confundus({x1}, {y})"))) and bool(
                list(pl.query(f"visited({x1}, {y})"))
            ):
                print("%", end=" ")
            else:
                print(".", end=" ")
            if bool(list(pl.query(f"stench({x1}, {y})"))):
                print("=", end=" ")
            else:
                print(".", end=" ")
            if bool(list(pl.query(f"tingle({x1}, {y})"))):
                print("T", end=" ")
            else:
                print(".", end=" ")
            print("| ", end="")
        print()

        print("| ", end="")
        for k in range(n_rooms):
            x1 = x + k
            if bool(list(pl.query(f"wall({x1}, {y})"))):
                print("# # #", end=" ")
                print("| ", end="")

                continue
            wumpus = bool(list(pl.query(f"wumpus({x1},{y})")))
            confundus = bool(list(pl.query(f"confundus({x1},{y})"))) and not (
                x1 == 0 and y == 0
            )
            agent = list(pl.query(f"current({x1},{y},D)"))
            if wumpus or confundus or bool(agent):
                print("—", end=" ")
                if bool(agent):
                    dir = agent[0]["D"]
                    if dir == "rnorth":
                        print("^", end=" ")
                    elif dir == "reast":
                        print(">", end=" ")
                    elif dir == "rsouth":
                        print("V", end=" ")
                    elif dir == "rwest":
                        print("<", end=" ")
                elif wumpus and confundus:
                    print("U", end=" ")
                elif wumpus:
                    print("W", end=" ")
                elif confundus:
                    print("O", end=" ")
                print("—", end=" ")
            else:
                print(".", end=" ")
                if bool(list(pl.query(f"visited({x1},{y})"))):
                    print("S", end=" ")
                elif bool(list(pl.query(f"safe({x1},{y})"))):
                    print("s", end=" ")
                else:
                    print("?", end=" ")
                print(".", end=" ")
            print("| ", end="")
        print()

        print("| ", end="")
        for k in range(n_rooms):
            x1 = x + k
            if bool(list(pl.query(f"wall({x1}, {y})"))):
                print("# # #", end=" ")
                print("| ", end="")
                continue
            if bool(list(pl.query(f"glitter({x1}, {y})"))):
                print("*", end=" ")
            else:
                print(".", end=" ")
            agent = bool(list(pl.query(f"current({x1},{y},D)")))
            if agent:
                try:
                    cur = list(pl.query("current(X,Y,D)"))
                    if cur[0] == cur[1]:
                        print("B", end=" ")
                    else:
                        print(".", end=" ")
                except IndexError:
                    print(".", end=" ")

                n_wumpus = len(list(pl.query("wumpus(X,Y)")))
                arrow = bool(list(pl.query("hasarrow")))
                if (
                    agent
                    and arrow == False
                    and n_wumpus == 0
                    and self.start_scream == 1
                ):
                    print("@", end=" ")
                    self.start_scream = 0
                else:
                    print(".", end=" ")
            else:
                print(".", end=" ")
                print(".", end=" ")

            print("| ", end="")
        print()

    def heardScream(self):
        self.start_scream = 1


def main():
    rows = 7
    columns = 6
    cell = 9
    relative_rows = 3
    relative_columns = 3
    map = AbsoluteMap(rows, columns, cell)
    relativeMap = RelativeMap(relative_rows, relative_columns, cell)
    npc = Utils()
    agent = Agent(map, relativeMap)
    map.mapCreation()
    map.initialisation(npc, agent)
    map.restartGame()

    print("Run step by step: 1")
    print("Run through: 2")
    print()
    runType = input("Available Inputs - 1 and 2: ")
    if runType == "1":
        agent.endGame = False
        while agent.endGame == False:
            agent.runStepbyStep()
    elif runType == "2":
        agent.endGame = False
        while agent.endGame == False:
            agent.runThrough()


if __name__ == "__main__":
    main()
