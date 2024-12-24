
from collections import Counter

from bidict import bidict

MappingIds = {

           'a2' : 1,
           'b2' : 2,
           'c2' : 3,
           'd2' : 4,
           'e2' : 5,
           'f2' : 6,
           'g2' : 7,
           'h2' : 8,
           'a7' : 9,
           'b7' : 10,
           'c7' : 11,
           'd7' : 12,
           'e7' : 13,
           'f7' : 14,
           'g7' : 15,
           'h7' : 16,
           
           # rooks
           'a1' : 17,
           'h1' : 18,
           'a8' : 19,
           'h8' : 20,
           
           # knights
           'b1' : 21,
           'g1' : 22,
           'b8' : 23,
           'g8' : 24,

           #bishops
           'c1' : 25,
           'f1' : 26,
           'c8' : 27,
           'f8' : 28,

           #queens
           'd1' : 29,
           'd8' : 30,
           
           #kings
           'e1' : 31,
           'e8' : 32

}

MappingIds = bidict(MappingIds)

MappingSquares = MappingIds.inverse


GettingIdsFromBoard = {}

totalpoints= Counter()