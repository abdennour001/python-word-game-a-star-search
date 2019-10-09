########################
# fibheap.py
#
# An implementation of a Fibonacci heap.
# Fibonacci heaps do decrease-key operations
# in amortized constant time, making them
# more suitable for A* search than Python's
# heapq module, which requires a linear-time
# re-heap operation for every decrease-key or
# arbitrary deletion.
#
# Written: Mark Wilson
########################

"""This is the fibheap module.  It defines classes for a Fibonacci heap and
nodes in the heap.  A Fibonacci heap is a min-heap with special running-time
constraints that make it more suitable for certain applications than Python's
built-in heapq module."""

import sys
import weakref

# A node in the Fibonacci heap.
class FibonacciNode:
	"""Represents a node in a FibonacciHeap.  The key and data values that are
	stored in the node are available as "node.key" and "node.data" respectively.
	Users generally should not need other members of this type.

	Usually you will not need to create a FibonacciNode directly (see
	FibonacciHeap.insert()).  Nor should you manipulate its members directly --
	see FibonacciHeap for member functions that manipulate node values."""

	def __init__(self, key, data=None, parent=None):
		"""Sets up a new, unmarked node with the given key, data value, parent
		node, and an empty list of children.

		Values of interest to the user are probably key and data values, which
		are stored internally at "node.key" and "node.data" respectively."""

		self.key = key
		self.data = data
		# Since parent holds a ref to children, we want a weak reference
		self.parent = weakref.ref(parent) if parent else parent
		self.children = []
		self.marked = False

# A Fibonacci heap.
class FibonacciHeap:
	"""A Fibonacci heap is a special data structure that functions as a
	min-heap but, unlike the standard binomial heap, can do decrease-key or
	delete operations on arbitrary heap nodes in amortized constant and log-n
	time, respectively.  This makes it particularly well-suited for
	applications like an A* search where arbitrary values in the heap may
	need to be revised online."""

	def __init__(self):
		"""Creates a new, empty Fibonacci heap."""

		# roots is a set for fast lookups and set operations -- contains
		# the root nodes for all trees in the heap.
		self.roots = set()
		# reference to the current minimal node
		self.minimum = None

	def is_empty(self):
		"""Returns True if the heap is empty, otherwise False."""

		return len(self.roots) == 0

	def clear(self):
		"""Empties the heap."""

		self.roots = set()
		self.minimum = None

	# Internal operation -- won't HURT for users to call this (it should
	# be a no-op from the user's perspective), but doesn't help and wastes time.
	#
	# Finds the minimum-valued node in the current root set.
	def find_minimum(self):
		"""This is an internal function that the user should never have to call.
		From the user's perspective it should be a somewhat expensive no-op."""

		if len(self.roots) == 0:
			self.minimum = None
			return
		for n in self.roots:
			if self.minimum == None or n.key < self.minimum.key:
				self.minimum = n

	# Merges this heap with another heap.
	def merge(self, other):
		"""Merges this heap with FibonacciHeap "other".  After the merge,
		the nodes from both heaps will be contained in this heap."""

		# Add the other heap's roots
		self.roots &= other.roots
		# The minimal node is one of our minimum or the other's minimum.
		if len(self.roots) == 0:
			self.minimum = None
			return
		if self.minimum == None:
			self.minimum = other.minimum
			return
		if other.minimum == None:
			return
		if other.minimum.key < self.minimum.key:
			self.minimum = other.minimum

	# Inserts a new node into the heap with the given key and data.  Returns
	# the new FibonacciNode created.
	def insert(self, key, data):
		"""Inserts a new node into the heap with the given key and data value.
		Returns the FibonacciNode holding the given values. Operates in
		amortized constant time."""

		# Just make a node and add it to the roots.
		n = FibonacciNode(key,data)
		self.roots.add(n)
		# Update minimum if appropriate
		if self.minimum == None or n.key < self.minimum.key:
			self.minimum = n
		return n

	# Returns the minimal node (key, data) but does not remove it.
	def peek_minimum(self):
		"""Returns the (key, data) pair of the minimally-valued FibonacciNode
		in the heap, but does not remove the min-node."""

		return (self.minimum.key, self.minimum.data)

	# Removes and returns the minimal node (key, data) in the heap.
	def extract_minimum(self):
		"""Returns the (key, data) pair of the minimally-valued FibonacciNode
		in the heap, and removes that node from the heap.  Operates in
		amortized O(log n) time."""

		# Grab the minimal node
		m = self.minimum
		# Remove the minimal node, reset the reference to it, and
		# reparent its children to be root nodes.
		self.roots.remove(m)
		self.minimum = None
		for c in m.children:
			c.parent = None
			c.marked = False
			self.roots.add(c)
		m.children = []

		# Iterate over the root list, checking for nodes with the same degree.
		# When nodes with the same degree are found, make the one with the
		# larger key a child of the other.
		# Repeat until no roots with the same degree exist.
		collision = True
		while collision:
			# Map from degree values to root nodes
			degreeDict = {}
			# not safe to remove from an iterable while we iterate over it.
			# Thus keep a set of nodes to be removed and take them all out
			# at the end.
			removedRoots = set()
			for n in self.roots:
				deg = len(n.children)
				if deg in degreeDict:
					if degreeDict[deg].key < n.key:
						smaller = degreeDict[deg]
						larger = n
					else:
						smaller = n
						larger = degreeDict[deg]
					smaller.children.append(larger)
					larger.parent = weakref.ref(smaller)
					degreeDict[deg] = smaller
					removedRoots.add(larger)
				else:
					degreeDict[deg] = n
			collision = (len(removedRoots) != 0)
			self.roots -= removedRoots

		# Find the new minimum node
		self.find_minimum()
		# Return the old minimum node
		return (m.key, m.data)

	# An internal operation -- should never be called by the user!
	#
	# Removes given node from its parent, makes it a root node, and returns
	# the parent node.
	def cut_node(self, node):
		"""This is an internal function.  Users should NEVER call this function,
		as it will probably violate all kinds of heap properties."""

		if node.parent == None:
			raise RuntimeError("Node to be cut is already root")
		p = node.parent()
		p.children.remove(node)
		node.parent = None
		node.marked = False
		self.roots.add(node)
		if node.key < self.minimum.key:
			self.minimum = node
		return p

	def decrease_key(self, node, key):
		"""Decreases the key on the given node to the new value.  Operates in
		amortized constant time."""

		if key >= node.key:
			raise RuntimeError("New key must be less than old key: %f >= %f" \
								% (key, node.key))

		node.key = key
		if node.parent == None:
			if node.key < self.minimum.key:
				self.minimum = node
			return
		if node.key >= node.parent().key:
			return

		n = self.cut_node(node)
		while n.marked:
			n = self.cut_node(n)

		if n.parent != None:
			n.marked = True

	def delete(self, node):
		"""Deletes the given node from the tree.  Operates in amortized O(log n)
		time."""
		self.decrease_key(node, sys.float_info.min)
		self.extract_minimum()
