# Simple patricia tree implementation for a ultra-fast strings.
# Maintains a patricia tree of strings; an individual string is
# just an index into this table.

class Node:
    def __init__(self):
        self.s = " "
        self.maxbit = 0
        self.bit = 0
        self.kids = []
        self.kids.append(0)
        self.kids.append(0)

class StringAtomTree:
  BITS  = 1
  NODES = 1 << BITS
  CHAR_BIT = 8
  
  def __init__(self):
      self.tree_ = []
      self.tree_.append(Node())

  def bits(self, p, maxbit, start, n):
      if start > maxbit:
          return 0
      return (ord(p[start/StringAtomTree.CHAR_BIT]) \
              >> (StringAtomTree.CHAR_BIT-start%StringAtomTree.CHAR_BIT-n)) \
              & ~(~0 << n)

  def clear(self):
      while(len(self.tree_)):
          self.tree_.pop()
      self.tree_.append(Node())

  def insert(self, s):
      maxbit = len(s) * StringAtomTree.CHAR_BIT - 1
      t = self.tree_[0].kids[0]
      p = 0
      i = 0

      while (self.tree_[p].bit < self.tree_[t].bit):
          kid = self.bits(s, maxbit, self.tree_[t].bit, StringAtomTree.BITS)
          p = t
          t = self.tree_[t].kids[kid]

      if s == self.tree_[t].s:
          return t

      while (self.bits(self.tree_[t].s, self.tree_[t].maxbit, i, 1) == self.bits(s, maxbit, i, 1)):
          i += 1

      p = 0
      x = self.tree_[0].kids[0]
      while self.tree_[p].bit < self.tree_[x].bit and (self.tree_[x].bit < i):
          kid = self.bits(s, maxbit, self.tree_[x].bit, StringAtomTree.BITS)
          p = x
          x = self.tree_[x].kids[kid]

      ibit = self.bits(s, maxbit, i, 1)
      self.tree_.append(Node())
      t = len(self.tree_)-1
      n = self.tree_[-1]
      n.s = s
      n.bit = i
      n.maxbit = maxbit
      n.kids[0] = x if ibit else t
      n.kids[1] = t if ibit else x
      self.tree_[p].kids[self.bits(s, maxbit, self.tree_[p].bit, 1)] = t
      return t

  def search(self, s):
    maxbit = len(s) * StringAtomTree.CHAR_BIT - 1;
    p = 0
    x = self.tree_[0].kids[0]
    while self.tree_[p].bit < self.tree_[x].bit:
      kid = self.bits(s, maxbit, self.tree_[x].bit, StringAtomTree.BITS)
      p = x
      x = self.tree_[x].kids[kid]

    if s == self.tree_[x].s:
        return x
    else:
      return ~0

  def key(self, index):
      return self.tree_[index].s

  def size(self):
      return len(self.tree_)

  def dump(self):
      for n in range(0, len(self.tree_)):
          t = self.tree_[n]
          print "Node %d:\n  string: %s\n  bit: %d\n  kid[0]: %d\n  kid[1]: %d\n" %\
          (n, t.s, t.bit, t.kids[0], t.kids[1])

class StringAtom:
    TestOnlyTag = 0
    
    def __init__(self):
        self.tree_ = StringAtomTree()
        self.index_ = 0

    def __init__(self, tree, s, test):
        self.tree_ = tree
        if test == StringAtom.TestOnlyTag:
            self.index_ = self.tree_.search(s)
        else:
            self.index_ = self.tree_.insert(s)
        if self.index_ == ~0:
            self.index_ = 0

    def index(self):
        return self.index_

    def string(self):
        assert tree_ !=0
        assert index_ != ~0
        return self.tree_.key(self.index_)

    def size(self):
        return len(self.string())

def test():
    sat = StringAtomTree()
    sat.insert("marco")
    sat.insert("matilde")
    sat.insert("cate")
    sat.insert("stefano")
    sat.insert("elena")

    sat.dump()
    

if __name__ == "__main__":
    test()
