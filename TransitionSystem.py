import Node
import DFA
from collections import deque


class TransitionSystem:
    # @brief    A class representing a transition system DFA abstraction
    #
    # For our purposes, this class represents the car-road transition system,
    # with all possible lane changes and choices of velocity allowed

    #
    # @brief      Constructs the TransitionSystem object.
    #
    # @param      self             The TransitionSystem object instance
    # @param      initCarX         The initial carX state. CarX ~ lane on
    #                              highway
    # @param      initCarY         The initial carY state. CarY ~ distance down
    #                              highway
    # @param      initCarT         The initial carT state. CarT ~ time step
    # @param      initCarVel       The initial velocity of the car
    # @param      maxTime          The maximum time step allowed
    # @param      allLanes         A list of all possible lane numbers on the
    #                              highway.
    # @param      allVelocities    A list of all possible car velocities for
    #                              ALL lanes
    # @param      allowedLaneVels  The allowed lane velocities tuple for a
    #                              certain lane number
    # @param      goalStates       The goal states for the car
    # @param      POS              The POS (physical occupancy set) object
    #                              which contains the 3D projection of a Node
    #                              state onto the x, y, and time grid for the
    #                              empty road.
    #
    def __init__(self, initCarX, initCarY, initCarT, initCarVel,
                 maxTime, allLanes, allVelocities, allowedLaneVels,
                 goalStates, POS):

        newNodeState = Node.NodeState(initCarX, initCarY, carT=0,
                                      prevLane=initCarX, prevVel=initCarVel)

        newNodeObs = Node.Observation(atGoal=False, crashed=False,
                                      speeding=False)

        initNode = Node.Node(state=newNodeState, obs=newNodeObs,
                             isVisited=False)
        Nodes = []
        Nodes.append(initNode)

        nodeQueue = deque()
        nodeQueue.append(initNode)
        atGoal = False

        while True:

            currNode = nodeQueue.popleft()
            allowedLanes = self.getAdjLanes(currNode.state.carX, allLanes)

            if (currNode.state.carT != maxTime):
                for lane in allowedLanes:
                    for vel in allVelocities:

                        # populate a new node at this state
                        currState = currNode.state
                        carX = lane
                        carY = currState.carY + vel
                        carT = currState.carT + 1
                        prevLane = currState.carX
                        prevVel = vel

                        nextState = Node.NodeState(carX=carX,
                                                   carY=carY,
                                                   carT=carT,
                                                   prevLane=prevLane,
                                                   prevVel=prevVel)

                        nextNode = Node.Node(state=nextState,
                                             isVisited=False,
                                             adjList=[])

                        allowedVelsPrevLane = allowedLaneVels[prevLane]
                        allowedVelsCarXLane = allowedLaneVels[carX]

                        # determining if there is crashing
                        minSpeedInPrevLane = min(allowedVelsPrevLane)
                        minSpeedInCarXLane = min(allowedVelsCarXLane)

                        crashed = self.crashed(prevLane, prevVel, carX, carY,
                                               carT, minSpeedInPrevLane,
                                               minSpeedInCarXLane, POS)
                        if not crashed:

                            # determining if there is speeding
                            speeding = self.speeding(prevLane, prevVel, carX,
                                                     allowedVelsPrevLane,
                                                     allowedVelsCarXLane)

                            # determining if the new state is in the goal state
                            atGoal = self.inGoalStates(carX, carY, goalStates)

                            # adding these observations to the new node
                            obs = Node.Observation(atGoal=atGoal,
                                                   crashed=crashed,
                                                   speeding=speeding)
                            nextNode.obs = obs

                            # need to add nextNode to the adj list of the node
                            # that reached nextNode (currNode), then get ready
                            # to build up nextNode
                            currNode.adjList.append(nextNode)
                            nodeQueue.append(nextNode)

            else:
                self.DFA = DFA.DFA(nodes=Nodes, startNode=initNode)
                return

    #
    # @brief      Calculates a boolean for whether the car is speeding
    #
    #             This boolean flag is used as one of the observations of the
    #             TransitionSystem itself.
    #
    # @param      self                 The TransitionSystem object instance
    # @param      prevLane             The lane the car was in during the
    #                                  previous time step
    # @param      prevVel              The previous velocity the car was
    #                                  traveling at during the previous time
    #                                  step
    # @param      carX                 The current carX value ~ lane on highway
    # @param      allowedVelsPrevLane  The set of legal velocities allowed in
    #                                  the prevLane lane
    # @param      allowedVelsCarXLane  The set of legal velocities allowed in
    #                                  the carX lane
    #
    # @return     @bool indicating whether or not the car was / is speeding in
    #             the prior or current time step
    #
    def speeding(self, prevLane, prevVel, carX, allowedVelsPrevLane,
                 allowedVelsCarXLane):

        if (prevVel in allowedVelsPrevLane) and \
           (prevVel in allowedVelsCarXLane):
            return False
        else:
            return True

    #
    # @brief      Calculates a boolean for whether the car is in one of the
    #             goal states along the road.
    #
    #             A goal state is a lane (x) and horizontal distance down the
    #             highway from the starting location (Y). These correspond to
    #             an exit on the highway the driver would like to use. This
    #             boolean flag is used as one of the observations of the
    #             TransitionSystem itself.
    #
    # @param      self        The TransitionSystem object instance
    # @param      carX        The current carX value ~ lane on highway
    # @param      carY        The current carY value ~ distance down highway
    # @param      goalStates  The set of goal states in x and y
    #
    # @return     @bool indicating whether or not the car is in one of the set
    #             of goalStates during current time step
    #
    def inGoalStates(self, carX, carY, goalStates):

        minYGoalState = goalStates[0][1]
        xGoalState = goalStates[0][0]
        if (carX == xGoalState) and (carY > minYGoalState):
            return True
        else:
            return False

    #
    # @brief      Calculates a boolean for whether the car has crashed into
    #             another one of the obstacle cars along the highway
    #
    #             This boolean flag is used as one of the observations of the
    #             TransitionSystem itself.
    #
    # @param      self                The TransitionSystem object instance
    # @param      prevLane            The previous lane for the car during the
    #                                 last time step
    # @param      prevVel             The previous velocity for the car during
    #                                 the last time step
    # @param      carX                The current carX value ~ lane on highway
    # @param      carY                The current carY value ~ distance down
    #                                 highway
    # @param      carT                The current carT value ~ current time
    #                                 step
    # @param      minSpeedInPrevLane  The minimum legal speed in the previous
    #                                 lane
    # @param      minSpeedInCarXLane  The minimum legal speed in the carX lane
    # @param      POS                 The POS (physical occupancy set) object
    #                                 which contains the 3D projection of a
    #                                 Node state onto the x, y, and time grid
    #                                 for the empty road.
    #
    # @return     @bool indicating whether or not the car will crash into
    #             another driver during the previous -> current time step if
    #             they take a certain control action
    #
    def crashed(self, prevLane, prevVel, carX, carY, carT,
                minSpeedInPrevLane, minSpeedInCarXLane, POS):

        # time steps are unit length for simplification
        timeStepLength = 1
        prevY = carY - prevVel * (timeStepLength)
        prevT = carT - timeStepLength

        # POS[x, y, t] = True (1) if another car is at the specific (x,y)
        # location of the road at time t
        distDownTheHwy = prevVel - minSpeedInPrevLane
        sumPrevLane = 0
        for ii in range(0, distDownTheHwy):
            sumPrevLane += POS[prevLane, prevY + ii, prevT]

        distDownTheHwy = prevVel - minSpeedInCarXLane
        sumCarXLane = 0
        for ii in range(0, distDownTheHwy):
            sumCarXLane += POS[carX, prevY + ii, prevT]

        numCollisions = sumPrevLane + sumCarXLane

        if numCollisions > 0:
            return True
        else:
            return False

    #
    # @brief      Returns a tuple of physically possible lanes to change to
    #
    # @param      self      The TransitionSystem object instance
    # @param      currLane  The car's current lane number
    # @param      allLanes  A tuple of all of the different lm
    #
    # @return     The physically meaningful, allowed adj lanes from currLane
    #
    def getAdjLanes(self, currLane, allLanes):

        maxLane = max(allLanes)
        minLane = min(allLanes)

        if currLane == maxLane:
            return (currLane - 1, currLane)
        elif currLane == minLane:
            return (currLane, currLane + 1)
        else:
            return (currLane - 1, currLane, currLane + 1)
