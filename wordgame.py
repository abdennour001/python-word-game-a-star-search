#!/usr/bin/env python

##########################
# wordgame.py
#
# An A* search to morph one word of
# length n into another word of length n,
# changing one letter at a time and using
# real words along the way.
#
# Invocation:  "wordgame.py word1 word2"
#
# Written: Mark Wilson
###########################


"""This is the wordgame module.  It defines an A* search for the change-one-
letter-at-a-time game.  The goal of the game is to get from word A to word B,
changing only one letter at a time and creating a new (actual) word at every
step.  For instance, to change from "mare" to "colt":
-mare
-more
-mole
-molt
-colt

This module is an executable script.  To run the program and solve an
instance of the game, execute the following at the command line:
> wordgame.py startword goalword

On Windows, you may need to execute with the "python" command:
> python wordgame.py startword goalword"""


import optparse

import astar_fibheap as astar

# Messages to be output to help the user
USAGE_MSG = \
"A script that solves a word-to-word morphing game by changing one letter\n"\
"at a time until the goal word is reached, taking steps only along real "\
"words.\n\n"\
"%prog [OPTIONS] WORD1 WORD2\n"
HEURISTIC_MSG = "Heuristic mode, one of 0 (null heuristic, h(N) = 0) or 1 "\
				"(custom heuristic, implemented by student).  Defaults to 0."

# A file containing a newline-delineated dictionary
DICT_FILENAME = 'words.txt'
# The letters of the alphabet
ALPHABET = [chr(i+97) for i in range(26)]
del i

#https://en.wikibooks.org/wiki/Algorithm_Implementation/Strings/Levenshtein_distance
def levenshtein(s1, s2):
		if len(s1) < len(s2):
				return levenshtein(s2, s1)

		# len(s1) >= len(s2)
		if len(s2) == 0:
				return len(s1)

		previous_row = range(len(s2) + 1)
		for i, c1 in enumerate(s1):
				current_row = [i + 1]
				for j, c2 in enumerate(s2):
						insertions = previous_row[j + 1] + 1 # j+1 instead of j since previous_row and current_row are one character longer
						deletions = current_row[j] + 1       # than s2
						substitutions = previous_row[j] + (c1 != c2)
						current_row.append(min(insertions, deletions, substitutions))
				previous_row = current_row
		return previous_row[-1]


#####################
#
# Returns a Python set object containing words of the given size,
# loaded from the file given by DICT_FILENAME.  Good for fast lookups
# of arbitrary strings to see if they're legal words.
#
def make_dictionary(size):
	"""Returns a Python set object containing words of the given size, loaded
	from the file whose name is given in the global variable DICT_FILENAME.
	This set object can be used for fast lookups of arbitrary strings to see
	if they're legal words (i.e., by using Python's "if VALUE in SET:"
	syntax)."""
	with open(DICT_FILENAME) as fin:
		words = fin.readlines()
	words = [w.strip().lower() for w in words if len(w.strip()) == size]
	return set(words)



######################
# WordState
#
# A state object for the search -- just contains the current word
# value under consideration.  It would be legal to just use the string
# representing the word, but this provides easier expandability, prevents confusion
# between a word and the search state representing that word, and gives more of a
# notion how the problem would be set up for a more complicated search space.
#
class WordState:
	"""A state class for the A* search, containing only the word value for
	the current state as a member variable named "word"."""

	def __init__(self, word):
		"""Initializes the object with the given word"""
		self.word = word








##############################
# WordAStar
#
# An A* search object for the word-search problem.  Initialize with the
# intended start and goal words, then call search().
#
class WordAStar(astar.AStar):
	"""A subclass of astar_fibheap.AStar to be used in the change-a-letter game.
	Uses WordState objects to represent search states."""

	def __init__(self, startWord, goalWord, heuristicType):
		"""Set up the A* search with the given start and goal words, which
		should be Python strings."""

		# Do some setup (parent constructor will fail otherwise, as it
		# relies on some values we need to define)
		if len(startWord) != len(goalWord):
			raise RuntimeError("Words must be the same length")
		self.sw = startWord
		self.gw = goalWord
		self.dictionary = make_dictionary(len(startWord))
		# Need to keep track of what states we've visited
		self.visited = {}
		state = WordState(startWord)
		# What heuristic should we use?
		self.heuristicType = heuristicType
		# Initialize generic A* search by calling parent constructor
		# with our first state
		astar.AStar.__init__(self, state)

	def is_goal(self, state):
		"""Returns True if the given state represents the goal word, otherwise
		False.  Internal;  users may call this method but there's no reason
		to."""
		if state.word == self.gw:
			return True
		return False

	def clear_visited(self):
		"""Clears the list of visited states.  Internal; users should NEVER
		call this method."""
		self.visited.clear()

	def visit(self, state, node):
		"""Notes the given state as visited and maps it to the given
		AStarNode.  Internal; users should NEVER call this method."""
		self.visited[state.word] = node

	def visited_state_node(self, state):
		"""If the given state has already been visited, return the associated
		AStarNode.  Otherwise, return None.  Internal; users can call this
		method but don't need to."""
 		if state.word in self.visited:
 			return self.visited[state.word]
		return None

	def heuristic_null(self, state):
		"""Returns a null heuristic (i.e., 0 for any state).  Internal; there
		is no reason for users to call this method."""
		return 0

	# IMPLEMENT ME!
	def heuristic_custom(self, state):
		"""Returns a custom heuristic value.  Internal; there is no reason for
		users to call this method.  Should be implemented by the student."""
		return levenshtein(state.word, self.gw)

	def heuristic(self, state):
		"""Return an admissible, consistent heuristic value for the given
		state, using our known goal word.  Dispatches to heuristic_null() or
		heuristic_custom() depending on command-line options.  Internal;
		users can call this method but don't need to."""

		if self.heuristicType == 0:
			return self.heuristic_null(state)
		elif self.heuristicType == 1:
			return self.heuristic_custom(state)
		else:
			raise RuntimeError("Illegal heuristic type: " \
								+ str(self.heuristicType))

	# IMPLEMENT ME!
	def successors(self, state):
		"""Return a tuple containing two lists:

		- A list of valid successor states (i.e., actual words of the correct
		length) for the given state
		- A corresponding list of costs to move to those states

		For example, if successor states were "mad" and "maw" and the costs to
		move to them were 2 and 3 respectively, this function returns:

		([WordState("mad"), WordState("maw")], [2, 3])

		NB:  The values given in this example are arbitrary for the sake of
		explanation and should not be taken as "good" or "correct"!  In particular,
		pay attention to the issue of returning correct costs for each step.

		Internal; users can safely call this method but have no reason to.  Should
		be implemented by the student."""

		successors_list = []
		costs_list = []
	
		for i in range(len(state.word)):
			word_list = list(state.word)
			for alph in ALPHABET:
				word_list[i] = alph
				if ''.join(word_list) in self.dictionary:
					successors_list.append(WordState(''.join(word_list)))
					costs_list.append(1)
		return (successors_list, costs_list)

	def branching_factor(self):
		"""Returns the average branching factor of the tree after a successful
		search."""
		bfs = self.node_bf(self.root)
		avgBF = float(sum(bfs)) / len(bfs)
		return avgBF

	def node_bf(self, node):
		bfs = [len(node.children)]
		for c in node.children:
			if c.expanded:
				bfs.extend(self.node_bf( c ))
		return bfs



####################
#
# Runs a search for words given in the arguments to the program invocation
#
def run_game():
	"""Runs a change-a-letter search for start and goal words given in the
	command-line arguments.  Called automatically when this module is
	invoked as a program."""

	parser = optparse.OptionParser(usage=USAGE_MSG)
	parser.add_option('-r', metavar='HEURISTIC', dest='heuristic',
						default='0', help=HEURISTIC_MSG)
	opts,args = parser.parse_args()
	if len(args) < 2:
		parser.print_help()
		return
	startWord = args[0].lower()
	goalWord = args[1].lower()

	search = WordAStar(startWord, goalWord, int(opts.heuristic))
	print "Starting search"
	if search.search():
		print "Search succeeded with", search.num_nodes(), "nodes"
		print "Average branching factor:", search.branching_factor()
		for state in search.result_path():
			print state.word
	else:
		print "Search failed -- no route between those words"

###################
#
# Handle invocation of this module
#
if __name__ == "__main__":
	run_game()
