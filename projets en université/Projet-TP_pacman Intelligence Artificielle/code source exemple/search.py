# -*- coding: utf-8 -*-

# search.py
# ---------
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
# 
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).

"""
In search.py, you will implement generic search algorithms which are called by
Pacman agents (in searchAgents.py).
"""

import util
from collections import defaultdict

class SearchProblem:
    """
    This class outlines the structure of a search problem, but doesn't implement
    any of the methods (in object-oriented terminology: an abstract class).

    You do not need to change anything in this class, ever.
    """

    def getStartState(self):
        """
        Returns the start state for the search problem.
        """
        util.raiseNotDefined()

    def isGoalState(self, state):
        """
          state: Search state

        Returns True if and only if the state is a valid goal state.
        """
        util.raiseNotDefined()

    def getSuccessors(self, state):
        """
          state: Search state

        For a given state, this should return a list of triples, (successor,
        action, stepCost), where 'successor' is a successor to the current
        state, 'action' is the action required to get there, and 'stepCost' is
        the incremental cost of expanding to that successor.
        """
        util.raiseNotDefined()

    def getCostOfActions(self, actions):
        """
         actions: A list of actions to take

        This method returns the total cost of a particular sequence of actions.
        The sequence must be composed of legal moves.
        """
        util.raiseNotDefined()


def tinyMazeSearch(problem):
    """
    Returns a sequence of moves that solves tinyMaze.  For any other maze, the
    sequence of moves will be incorrect, so only use this for tinyMaze.
    """
    from game import Directions
    s = Directions.SOUTH
    w = Directions.WEST
    return  [s, s, w, s, w, w, s, w]

def depthFirstSearch(problem):
    """
    Search the deepest nodes in the search tree first.

    Your search algorithm needs to return a list of actions that reaches the
    goal. Make sure to implement a graph search algorithm.

    To get started, you might want to try some of these simple commands to
    understand the search problem that is being passed in:

    print "Start:", problem.getStartState()
    print "Is the start a goal?", problem.isGoalState(problem.getStartState())
    print "Start's successors:", problem.getSuccessors(problem.getStartState())
    """
    "*** YOUR CODE HERE ***"
    
    from game import Directions
    frontier = util.Stack() #utilisation de LIFO queue
    start = problem.getStartState() #l'état initial du problème
    goal = start #l'état but du problème
    frontier.push(start) #Ajout du noeud start à la pile frontier
    
    explored = set() #Collection des noeuds explorés
    
    """
    Dictionnaire solution avec la clé est une état, et la valeur est un tuple (action, état)
    état dans le tuple est le prédécesseur de l'état clé
    action dans le tuple est l'action requise pour arriver à l'état clé de l'état dans le tuple
    Un état ici est un tuple de position (x, y)
    Cette dictionnaire stocke des actions et ses noeuds correspondants qui ont exploré
    """
    solution = dict() 
    while frontier: 
        
        node = frontier.pop() #Dépile un noeud de la pile frontier
        #print("Exploring Node: ", node)
        if problem.isGoalState(node): #Si ce noeud est l'état but
            goal = node #Affecter ce noeud à l'état but
            break
        explored.add(node) #Si ce noeud n'est pas l'état but, on l'ajoute à la collection explored
        #print("Successsors of node ", node, "is :", problem.getSuccessors(node))
        for child in problem.getSuccessors(node): #les successeurs de noeud node
            #print("Successors: ", problem.getSuccessors(node))
            
            if child[0] not in explored: #Si un successeur n'est pas dans la collection explored
                solution[child[0]] = (child[1], node) #On stocke ce successeur, son parent et 
                                            # l'action du parent vers ce successeur qui vient d'être exploré
                if problem.isGoalState(child): #Si ce noeud est l'état but
                    goal = child #Affecter ce noeud à l'état but
                    break
                if(child[0] not in frontier.list): # Si le successeur n'est pas dans la pile frontier
                    frontier.push(child[0]) # On empile ce successeur à la pile
          
    actions = util.Queue() #Les actions de l'état initial vers l'état but
    while(goal != start): #Tant que l''état but est différent de l'état initial
        actions.push(solution[goal][0]) #On ajoute l'action pour arriver à l'état but
        goal = solution[goal][1] #On change l'état but en l'état de son parent
    #print("Actions: ", actions.list)
    return actions.list
    
    util.raiseNotDefined()

def breadthFirstSearch(problem):
    """Search the shallowest nodes in the search tree first."""
    "*** YOUR CODE HERE ***"
    util.raiseNotDefined()

def uniformCostSearch(problem):
    """Search the node of least total cost first."""
    "*** YOUR CODE HERE ***"
    util.raiseNotDefined()

def nullHeuristic(state, problem=None):
    """
    A heuristic function estimates the cost from the current state to the nearest
    goal in the provided SearchProblem.  This heuristic is trivial.
    """
    return 0

def aStarSearch(problem, heuristic=nullHeuristic):
    """Search the node that has the lowest combined cost and heuristic first."""
    "*** YOUR CODE HERE ***"
    
    from game import Directions
    frontier = util.PriorityQueue() #utilisation de la structure de données PriorityQueue
                                    #sa priorité est la fonction d'évaluation f_n
    start = problem.getStartState() #l'état initial du problème
    goal = start #l'état but du problème
    path_cost = defaultdict(lambda: 0) #Une dictionnaire: clé: un noeud, 
                                        #valeur: le coût de chemin du noeud initial au noeud de sa clé
                                        #comme la valeur de la fonction g(n)
                                        #la valeur par défault des noeuds est 0
    frontier.push(start, 0 + heuristic(start, problem)) #Ajout du noeud start à la pile frontier
    
    explored = set() #Collection des noeuds explorés
    
    """
    Dictionnaire solution avec la clé est une état, et la valeur est un tuple (action, état, f_n)
    état dans le tuple est le prédécesseur de l'état clé
    action dans le tuple est l'action requise pour arriver à l'état clé de l'état dans le tuple
    f_n dans le tuple est la fonction d'évaluation du noeud clé
    Un état ici est un tuple de position (x, y)
    Cette dictionnaire stocke des actions et ses noeuds correspondants qui ont exploré
    """
    solution = dict() 
    while frontier:
        node = frontier.pop() #Dépile un noeud de la pile frontier
        if problem.isGoalState(node): #Si ce noeud est l'état but
            goal = node #Affecter ce noeud à l'état but
            break
        
        #print("Exploring Node: ", node)
        explored.add(node) #Si ce noeud n'est pas l'état but, on l'ajoute à la collection explored
        #print("Successsors of node ", node, "is :", problem.getSuccessors(node))
        for child in problem.getSuccessors(node): #les successeurs de noeud node
            if child[0] not in explored: #Si un successeur n'est pas dans la collection explored
                path_cost[child[0]] = path_cost[node] + child[2] #Ajout le coût de chemin du noeud initial au noeud successeur
                                                                #La valeur est égale au coût de chemin du noeud de son parent
                                                                #plus stepCost pour arriver à ce noeud de son parent
                f_n = path_cost[child[0]] + heuristic(child[0], problem) #la fonction d'évaluation f_n = g_n + h_n
                                                                        #g_n est la valeur path_cost(n)
                                                                        #h_n est la valeur de heuristic(n)
                if child[0] not in solution.keys(): #Si le successeur n'est pas stocké dans la dictionnaire solution
                    solution[child[0]] = (child[1], node, f_n) #On stocke ce successeur, son parent et
                                                              #l'action du parent vers ce successeur qui vient d'être explorée et
                                                              #la fonction d'évaluation de ce successeur
                else: #Si le successeur est déjà stocké dans la dictionnaire solution
                    if f_n <= solution[child[0]][2]: #Si f_n est plus petite que la valeur f_n précédente
                        solution[child[0]] = (child[1], node, f_n) #Mise à jour avec cette nouvelle valeur et
                                                                    #l'action, son parent qui vient d'être explorée
                #print "Heuristic of node ", child[0], "is: ", f_n
                frontier.update(child[0], f_n) #Insérer le successeur si ce noeud n'est pas dans la frontière
                                                #Si ce noeud est déjà dans la frontière
                                                #On remplace la valeur f_n de ce noeud si cette valeur est plus petite
                                                #que la valeur précédente f_n de ce noeud
        #print "\n"
    #print("Solution: ", solution)      
    actions = util.Queue() #Les actions de l'état initial vers l'état but
    while(goal != start): #Tant que l''état but est différent de l'état initial
        actions.push(solution[goal][0]) #On ajoute l'action pour arriver à l'état but
        goal = solution[goal][1] #On change l'état but en l'état de son parent
    #print("Actions: ", actions.list)
    return actions.list
    
    util.raiseNotDefined()


# Abbreviations
bfs = breadthFirstSearch
dfs = depthFirstSearch
astar = aStarSearch
ucs = uniformCostSearch
