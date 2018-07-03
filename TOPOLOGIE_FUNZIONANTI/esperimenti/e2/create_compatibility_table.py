def get_compatibility_table():
    C = {}

    C['R-R'] = {}
    C['R-R']['H-H'] = 'R-R'

    C['R-A'] = {}
    C['R-A']['R-A'] = 'R-A'
    C['R-A']['R-NC'] = 'R-A'
    C['R-A']['H-A'] = 'R-A'
    C['R-A']['H-NC'] = 'R-A'
    C['R-A']['H-H'] = 'R-A'
    
    C['A-R'] = {}
    C['A-R']['A-R'] = 'A-R'
    C['A-R']['NC-R'] = 'A-R'
    C['A-R']['A-H'] = 'A-R'
    C['A-R']['NC-H'] = 'A-R'
    C['A-R']['H-H'] = 'A-R'
    
    C['R-B'] = {}
    C['R-B']['R-B'] = 'R-B'
    C['R-B']['R-NC'] = 'R-B'
    C['R-B']['H-NC'] = 'R-B'
    C['R-B']['H-H'] = 'R-B'

    C['B-R'] = {}
    C['B-R']['B-R'] = 'B-R'
    C['B-R']['NC-R'] = 'B-R'
    C['B-R']['NC-H'] = 'B-R'
    C['B-R']['H-H'] = 'B-R'

    C['R-NC'] = {}
    C['R-NC']['R-A'] = 'R-A'
    C['R-NC']['R-B'] = 'R-B'
    C['R-NC']['R-NC'] = 'R-NC'
    C['R-NC']['H-NC'] = 'R-NC'
    C['R-NC']['H-H'] = 'R-NC'

    C['NC-R'] = {}
    C['NC-R']['A-R'] = 'A-R'
    C['NC-R']['B-R'] = 'B-R'
    C['NC-R']['NC-R'] = 'NC-R'
    C['NC-R']['NC-H'] = 'NC-R'
    C['NC-R']['H-H'] = 'NC-R'

    C['A-A'] = {}
    C['A-A']['A-A'] = 'A-A'
    C['A-A']['A-H'] = 'A-A'
    C['A-A']['H-A'] = 'A-A'
    C['A-A']['NC-NC'] = 'A-A'
    C['A-A']['NC-H'] = 'A-A'
    C['A-A']['H-NC'] = 'A-A'
    C['A-A']['H-H'] = 'A-A'
    C['A-A']['A-NC'] = 'A-A'
    C['A-A']['NC-A'] = 'A-A'
 
    C['A-H'] = {}
    C['A-H']['A-R'] = 'A-R'
    C['A-H']['NC-R'] = 'A-R'
    C['A-H']['A-A'] = 'A-A'
    C['A-H']['A-H'] = 'A-H'
    C['A-H']['H-A'] = 'A-A'
    C['A-H']['NC-NC'] = 'A-NC'
    C['A-H']['NC-H'] = 'A-H'
    C['A-H']['H-NC'] = 'A-NC'
    C['A-H']['H-H'] = 'A-H'
    C['A-H']['A-NC'] = 'A-NC'
    C['A-H']['NC-A'] = 'A-NC'
    C['A-H']['NC-B'] = 'A-B'
    C['A-H']['A-B'] = 'A-B'

    C['H-A'] = {}
    C['H-A']['R-A'] = 'R-A'
    C['H-A']['R-NC'] = 'R-A'
    C['H-A']['A-A'] = 'A-A'
    C['H-A']['A-H'] = 'A-A'
    C['H-A']['H-A'] = 'H-A'
    C['H-A']['NC-NC'] = 'NC-A'
    C['H-A']['NC-H'] = 'NC-A'
    C['H-A']['H-NC'] = 'H-A'
    C['H-A']['H-H'] = 'H-A'
    C['H-A']['A-NC'] = 'A-A'
    C['H-A']['NC-A'] = 'NC-A'
    C['H-A']['B-NC'] = 'B-A'
    C['H-A']['B-A'] = 'B-A'


    C['NC-NC'] = {}
    C['NC-NC']['A-A'] = 'A-A'
    C['NC-NC']['A-H'] = 'A-NC'
    C['NC-NC']['H-A'] = 'NC-A'
    C['NC-NC']['NC-NC'] = 'NC-NC'
    C['NC-NC']['NC-H'] = 'NC-NC'
    C['NC-NC']['H-H'] = 'NC-NC'
    C['NC-NC']['A-NC'] = 'A-NC'
    C['NC-NC']['B-NC'] = 'B-NC'
    C['NC-NC']['A-B'] = 'A-B'
    C['NC-NC']['H-NC'] = 'NC-NC'
    C['NC-NC']['NC-A'] = 'NC-A'
    C['NC-NC']['NC-B'] = 'NC-B'
    C['NC-NC']['B-A'] = 'B-A'

    C['NC-H'] = {}
    C['NC-H']['A-A'] = 'A-A'
    C['NC-H']['A-H'] = 'A-H'
    C['NC-H']['NC-NC'] = 'NC-NC'
    C['NC-H']['NC-H'] = 'NC-H'
    C['NC-H']['H-H'] = 'NC-H'
    C['NC-H']['A-NC'] = 'A-NC'
    C['NC-H']['B-NC'] = 'B-NC'
    C['NC-H']['A-B'] = 'A-B'
    C['NC-H']['A-R'] = 'A-R'
    C['NC-H']['B-R'] = 'B-R'
    C['NC-H']['NC-R'] = 'NC-R'
    C['NC-H']['H-A'] = 'NC-A'
    C['NC-H']['H-NC'] = 'NC-NC'
    C['NC-H']['NC-A'] = 'NC-A'
    C['NC-H']['NC-B'] = 'NC-B'
    C['NC-H']['B-A'] = 'B-A'

    C['H-NC'] = {}
    C['H-NC']['R-A'] = 'R-A'
    C['H-NC']['R-B'] = 'R-B'
    C['H-NC']['R-NC'] = 'R-NC'
    C['H-NC']['A-A'] = 'A-A'
    C['H-NC']['A-H'] = 'A-NC'
    C['H-NC']['H-A'] = 'H-A'
    C['H-NC']['NC-NC'] = 'NC-NC'
    C['H-NC']['NC-H'] = 'NC-NC'
    C['H-NC']['H-NC'] = 'H-NC'
    C['H-NC']['H-H'] = 'H-NC'
    C['H-NC']['A-NC'] = 'A-NC'
    C['H-NC']['NC-A'] = 'NC-A'
    C['H-NC']['B-NC'] = 'B-NC'
    C['H-NC']['NC-B'] = 'NC-B'
    C['H-NC']['A-B'] = 'A-B'
    C['H-NC']['B-A'] = 'B-A'


    C['H-H'] = {}
    C['H-H']['R-R'] = 'R-R'
    C['H-H']['R-A'] = 'R-A'
    C['H-H']['R-B'] = 'R-B'
    C['H-H']['R-NC'] = 'R-NC'
    C['H-H']['A-A'] = 'A-A'
    C['H-H']['A-H'] = 'A-H'
    C['H-H']['NC-NC'] = 'NC-NC'
    C['H-H']['NC-H'] = 'NC-H'
    C['H-H']['H-H'] = 'H-H'
    C['H-H']['A-NC'] = 'A-NC'
    C['H-H']['B-NC'] = 'B-NC'
    C['H-H']['A-B'] = 'A-B'
    C['H-H']['A-R'] = 'A-R'
    C['H-H']['B-R'] = 'B-R'
    C['H-H']['NC-R'] = 'NC-R'
    C['H-H']['H-A'] = 'H-A'
    C['H-H']['H-NC'] = 'H-NC'
    C['H-H']['NC-A'] = 'NC-A'
    C['H-H']['NC-B'] = 'NC-B'
    C['H-H']['B-A'] = 'B-A'

    C['A-NC'] = {}
    C['A-NC']['A-A'] = 'A-A'
    C['A-NC']['A-H'] = 'A-NC'
    C['A-NC']['NC-NC'] = 'A-NC'
    C['A-NC']['NC-H'] = 'A-NC'
    C['A-NC']['H-H'] = 'A-NC'
    C['A-NC']['A-NC'] = 'A-NC' 
    C['A-NC']['A-B'] = 'A-B'
    C['A-NC']['H-A'] = 'A-A'
    C['A-NC']['H-NC'] = 'A-NC'
    C['A-NC']['NC-A'] = 'A-A'
    C['A-NC']['NC-B'] = 'A-B'

    C['NC-A'] = {}
    C['NC-A']['A-A'] = 'A-A'
    C['NC-A']['A-H'] = 'A-A'
    C['NC-A']['H-A'] = 'NC-A'
    C['NC-A']['NC-NC'] = 'NC-A'
    C['NC-A']['NC-H'] = 'NC-A'
    C['NC-A']['H-NC'] = 'NC-A'
    C['NC-A']['H-H'] = 'NC-A'
    C['NC-A']['A-NC'] = 'A-A'
    C['NC-A']['NC-A'] = 'NC-A'
    C['NC-A']['B-NC'] = 'B-A'
    C['NC-A']['B-A'] = 'B-A'

    C['B-NC'] = {} 
    C['B-NC']['NC-NC'] = 'B-NC'
    C['B-NC']['NC-H'] = 'B-NC'
    C['B-NC']['H-H'] = 'B-NC'   
    C['B-NC']['B-NC'] = 'B-NC'
    C['B-NC']['H-A'] = 'B-A'
    C['B-NC']['H-NC'] = 'B-NC'
    C['B-NC']['NC-A'] = 'B-A'
    C['B-NC']['NC-B'] = 'B-B'
    C['B-NC']['B-A'] = 'B-A'

    C['NC-B'] = {} 
    C['NC-B']['A-H'] = 'A-B'
    C['NC-B']['NC-NC'] = 'NC-B'
    C['NC-B']['NC-H'] = 'NC-B'
    C['NC-B']['H-NC'] = 'NC-B'
    C['NC-B']['H-H'] = 'NC-B'
    C['NC-B']['A-NC'] = 'A-B'
    C['NC-B']['B-NC'] = 'B-B'
    C['NC-B']['NC-B'] = 'NC-B'
    C['NC-B']['A-B'] = 'A-B'

    C['A-B'] = {}
    C['A-B']['A-H'] = 'A-B'
    C['A-B']['NC-NC'] = 'A-B'
    C['A-B']['NC-H'] = 'A-B'
    C['A-B']['H-H'] = 'A-B'
    C['A-B']['A-NC'] = 'A-B' 
    C['A-B']['A-B'] = 'A-B'
    C['A-B']['H-NC'] = 'A-B'
    C['A-B']['NC-B'] = 'A-B'

    C['B-A'] = {}
    C['B-A']['H-A'] = 'B-A'
    C['B-A']['NC-NC'] = 'B-A'
    C['B-A']['NC-H'] = 'B-A'
    C['B-A']['H-NC'] = 'B-A'
    C['B-A']['H-H'] = 'B-A'
    C['B-A']['NC-A'] = 'B-A'
    C['B-A']['B-NC'] = 'B-A'
    C['B-A']['B-A'] = 'B-A'

    return C
