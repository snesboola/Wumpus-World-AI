:-dynamic([
  visited/2,
  glitter/2,
  tingle/2,
  stench/2,
  confundus/2,
  wall/2,
  safe/2,
  current/3,
  wumpus/2,
  wumpusLocation/2, %% exact wumpus cell

  %% Flags to track the progression of the game

  killedWumpus/0, %% flag to see if wumpus has been killed
  wumpusNotExist/2,
  confundusNotExist/2,
  numStenchCells/1, %% tracks number of stench cells visited
  hasarrow/0,
  wumpusLocated/0, %% flag to see if wumpus has been located
  max_moves/1, %% limit number of moves before giving up
  go_to_origin/0, %% give up flag
  risk/0 %% risk flag
]).


reborn:-
  retractall(visited(_,_)),
  retractall(glitter(_,_)),
  retractall(tingle(_,_)),
  retractall(stench(_,_)),
  retractall(confundus(_,_)),
  retractall(wall(_,_)),
  retractall(safe(_,_)),
  retractall(current(_,_,_)),
  retractall(wumpus(_,_)),
  retractall(wumpusLocation(_,_)),
  retractall(numStenchCells(_)),
  retractall(confundusNotExist(_,_)),
  retractall(wumpusNotExist(_,_)),
  retractall(max_moves(_)),
  retractall(go_to_origin),
  retractall(risk),
  retractall(wumpusLocated),
  assert(current(0,0,rnorth)),
  assert(safe(0,0)),
  assert(visited(0,0)),
  assert(numStenchCells(0)),
  assert(max_moves(500)),
  retractall(killedWumpus),
  assert(hasarrow).

reposition(L):-
  retractall(visited(_,_)),
  retractall(glitter(_,_)),
  retractall(tingle(_,_)),
  retractall(stench(_,_)),
  retractall(confundus(_,_)),
  retractall(wall(_,_)),
  retractall(safe(_,_)),
  retractall(current(_,_,_)),
  retractall(wumpus(_,_)),
  retractall(wumpusLocation(_,_)),
  retractall(numStenchCells(_)),
  retractall(confundusNotExist(_,_)),
  retractall(wumpusNotExist(_,_)),
  retractall(max_moves(_)),
  retractall(go_to_origin),
  retractall(risk),
  retractall(wumpusLocated),
  assert(current(0,0,rnorth)),
  assert(safe(0,0)),
  assert(visited(0,0)),
  assert(numStenchCells(0)),
  assert(max_moves(500)),
  [_, St, Tgl, Gl, _, _] = L,
  markStenchCell(St), manage_tingle(Tgl), manage_glitter(Gl).

%% kill wumpus if arrow is fired in his direction, in a straight line
loop(M,N,BaseX,BaseY,Xoffset,Yoffset):-
  between(M, N, I),
  New_X is BaseX + (I * Xoffset),
  New_Y is BaseY + (I * Yoffset),
  retract_wumpus(New_X,New_Y),
  I >= N, !.
  loop(M,I,BaseX,BaseY,Xoffset,Yoffset).

%% agent may begin to take risks as the game drags on longer without a solution
move_counter:-
  max_moves(N), A is N-1,
  (
    (A == 0, assert(go_to_origin)); (A == 100, assert(risk)); true
  ),
  retract(max_moves(N)), assert(max_moves(A)).

%% walls cannot be marked the same way as other objects or wumpus
is_wall(X,Y):-
  (
    \+wall(X,Y), assert(wall(X,Y)),
    (
      (confundus(X,Y), wumpus(X,Y), retract(confundus(X,Y)), retract(wall(X,Y)));
      (confundus(X,Y), retract(confundus(X,Y)));
      (wumpus(X,Y), retract(wumpus(X,Y)));
      true
    ),
    (
      (\+wumpusNotExist(X,Y), \+confundusNotExist(X,Y), assert(wumpusNotExist(X,Y)), assert(confundusNotExist(X,Y)));
      (\+wumpusNotExist(X,Y), assert(wumpusNotExist(X,Y)));
      (\+confundusNotExist(X,Y), assert(confundusNotExist(X,Y)));
      true
    )
  );
  true.


move(A,L):-
  [Cfdus, St, Tgl, Gl, Bump, Sc] = L,
  (
    current(X, Y, D),
    (A == moveforward -> (
      Bump == on -> (
        ((D == rnorth, New_Y is Y+1, is_wall(X,New_Y), false) ;
        (D == reast, New_X is X+1, is_wall(New_X,Y), false) ;
        (D == rsouth, New_Y is Y-1, is_wall(X,New_Y), false) ;
        (D == rwest, New_X is X-1, is_wall(New_X,Y)))
      ) ; Cfdus == on -> reposition(L); goforward, move_counter, markStenchCell(St), manage_tingle(Tgl), manage_glitter(Gl)
    ),
    retract_portal(X,Y), retract_wumpus(X,Y), !);
    (A == shoot -> retractall(hasarrow), (Sc == on -> (
      assert(killedWumpus),
      (
        wumpusLocation(X,Y),
        (retractall(wumpus(_,_)); true),
        (retractall(wumpusLocation(_,_)); true),
        (retractall(stench(_,_)); true),
        assert(safe(X,Y))
      )
    ); (
      (
        (D == rnorth, loop(1, 20, X, Y, 0, 1));
        (D == rsouth, loop(1, 20, X, Y, 0, -1));
        (D == reast, loop(1, 20, X, Y, 1, 0));
        (D == rwest, loop(1, 20, X, Y, -1, 0))
      )
    )), !);
    (A == turnleft -> turn(turnleft), !);
    (A == turnright -> turn(turnright), !);
    (A == pickup -> retract(glitter(X,Y)), !)
  ).

turn(Face):-
  current(X,Y,D),
  (
    (Face == turnright,
      (
        (D == rnorth, retract(current(X,Y,D)), assert(current(X,Y,reast)), !);
        (D == reast, retract(current(X,Y,D)), assert(current(X,Y,rsouth)), !);
        (D == rsouth, retract(current(X,Y,D)), assert(current(X,Y,rwest)), !);
        (D == rwest, retract(current(X,Y,D)), assert(current(X,Y,rnorth)))
      ));
    (Face == turnleft,
      (
        (D == rnorth, retract(current(X,Y,D)), assert(current(X,Y,rwest)), !);
        (D == reast, retract(current(X,Y,D)), assert(current(X,Y,rnorth)), !);
        (D == rsouth, retract(current(X,Y,D)), assert(current(X,Y,reast)), !);
        (D == rwest, retract(current(X,Y,D)), assert(current(X,Y,rsouth)))
      ))
  ).

retract_wumpus(X,Y):-
  ((wumpus(X,Y), retract(wumpus(X,Y))); true),
  ((\+wumpusNotExist(X,Y), assert(wumpusNotExist(X,Y))); true),
  ((\+safe(X,Y), wumpusNotExist(X,Y), confundusNotExist(X,Y), assert(safe(X,Y))); true).

retract_portal(X,Y):-
  ((confundus(X,Y), retract(confundus(X,Y))); true),
  ((\+confundusNotExist(X,Y), assert(confundusNotExist(X,Y))); true),
  ((\+safe(X,Y), wumpusNotExist(X,Y), confundusNotExist(X,Y), assert(safe(X,Y))); true).

%% this marks cells with a stench, to be used later to locate wumpus location
markStenchCell(State):-
  current(X,Y,_),
  X_W is X-1, X_E is X+1, Y_N is Y+1, Y_S is Y-1,
  (State == on -> (
    (\+visited(X_W,Y), \+wumpus(X_W,Y), \+tingle(X_W,Y), \+wall(X_W,Y), \+wumpusNotExist(X_W,Y), \+wumpusLocated, \+killedWumpus, assert(wumpus(X_W,Y)), false) ;
    (\+visited(X_E,Y), \+wumpus(X_E,Y), \+tingle(X_E,Y), \+wall(X_E,Y), \+wumpusNotExist(X_E,Y), \+wumpusLocated, \+killedWumpus, assert(wumpus(X_E,Y)), false) ;
    (\+visited(X,Y_N), \+wumpus(X,Y_N), \+tingle(X,Y_N), \+wall(X,Y_N), \+wumpusNotExist(X,Y_N), \+wumpusLocated, \+killedWumpus, assert(wumpus(X,Y_N)), false) ;
    (\+visited(X,Y_S), \+wumpus(X,Y_S), \+tingle(X,Y_S), \+wall(X,Y_S), \+wumpusNotExist(X,Y_S), \+wumpusLocated, \+killedWumpus, assert(wumpus(X,Y_S)), false) ;
    ((\+stench(X,Y), assert(stench(X,Y)), numStenchCells(N), NewN is N+1, retract(numStenchCells(N)), assert(numStenchCells(NewN))), false) ;
    locate_wumpus
  );
  (retract_wumpus(X_W,Y), retract_wumpus(X_E,Y), retract_wumpus(X,Y_N), retract_wumpus(X,Y_S))
  );
  true.

manage_glitter(State):-
  (State == on, current(X,Y,_), \+glitter(X,Y), assert(glitter(X,Y)));
  true.

manage_tingle(State):-
  current(X,Y,_),
  X_W is X-1, X_E is X+1, Y_N is Y+1, Y_S is Y-1,
  (State == on -> (
    ( \+visited(X_W,Y), \+confundus(X_W,Y), \+tingle(X_W,Y), \+wall(X_W,Y), \+confundusNotExist(X_W,Y), assert(confundus(X_W,Y)), false) ;
    ( \+visited(X_E,Y), \+confundus(X_E,Y), \+tingle(X_E,Y), \+wall(X_E,Y), \+confundusNotExist(X_E,Y), assert(confundus(X_E,Y)), false) ;
    ( \+visited(X,Y_N), \+confundus(X,Y_N), \+tingle(X,Y_N), \+wall(X,Y_N), \+confundusNotExist(X,Y_N), assert(confundus(X,Y_N)), false) ;
    ( \+visited(X,Y_S), \+confundus(X,Y_S), \+tingle(X,Y_S), \+wall(X,Y_S), \+confundusNotExist(X,Y_S), assert(confundus(X,Y_S)), false) ;
    ( \+tingle(X,Y), assert(tingle(X,Y)); true)
  );
    (retract_portal(X_W,Y), retract_portal(X_E,Y), retract_portal(X,Y_N), retract_portal(X,Y_S))
  );
  true.

%% function to locate wumpus
locate_wumpus:-
  findall([Xn,Yn], stench(Xn,Yn), Coords),
  \+wumpusLocated -> (
    (numStenchCells(2) -> findWump2stench(Coords); true),
    wumpusLocated -> (wumpusLocation(X,Y), retractall(wumpus(_,_)),assert(wumpus(X,Y))); true); true.

%% this helps to locate wumpus using 2 cells that have the stench property
findWump2stench(Coords):-
  nth0(0, Coords, First),
  nth0(1, Coords, Second),
  nth0(0, First, Firstx),
  nth0(0, Second, Secondx),
  nth0(1, First, Firsty),
  nth0(1, Second, Secondy),
  (
    (Firstx == Secondx, Xw is Firstx, Yw is (Firsty + Secondy)/2, assert(wumpusLocation(Xw,Yw)), assert(wumpusLocated), !);
    (Firsty == Secondy, Xw is (Firstx + Secondx)/2, Yw is Firsty, assert(wumpusLocation(Xw,Yw)), assert(wumpusLocated), !)
  ).

give_up(L):-
  current(X,Y,D),
  X_W is X-1, X_E is X+1, Y_N is Y+1, Y_S is Y-1,
  (
    (X_W == 0, Y == 0, move_Rwest(L));
    (X == 0, Y_S == 0, move_Rsouth(L));
    (X_E == 0, Y == 0, move_Reast(L));
    (X == 0, Y_N == 0, move_Rnorth(L));
    (X == 0, Y == 0, face_Rnorth(L))
  );
  plan(L).

%% agent can choose either to continue or give up
explore(L):-
  (current(Xcur,Ycur,Dcur), go_to_origin, Xcur == 0, Ycur == 0, Dcur == rnorth) -> false;
  (
    current(X,Y,_),
    (
      (glitter(X,Y), A = pickup);
      (go_to_origin, give_up(A));
      (stench(X,Y), danger(A));
      plan(A)
    ),
    L = [A]
  ).

goforward:-
  current(X,Y,D),
  (
    (D == rnorth, New_Y is Y+1, retract(current(X,Y,D)), assert((current(X,New_Y,D))), assert(visited(X,New_Y)), !);
    (D == reast, New_X is X+1, retract(current(X,Y,D)), assert((current(New_X,Y,D))), assert(visited(New_X,Y)), !);
    (D == rsouth, New_Y is Y-1, retract(current(X,Y,D)), assert((current(X,New_Y,D))), assert(visited(X,New_Y)), !);
    (D == rwest, New_X is X-1, retract(current(X,Y,D)), assert((current(New_X,Y,D))), assert(visited(New_X,Y)))
  ).

face_Rnorth(L):-
  L = turnleft.

move_Rwest(L):-
  current(_,_,D),
  D == rwest -> L = moveforward;
  L = turnright.

move_Reast(L):-
  current(_,_,D),
  D == reast -> L = moveforward;
  L = turnright.

move_Rsouth(L):-
  current(_,_,D),
  D == rsouth -> L = moveforward;
  L = turnright.

move_Rnorth(L):-
  current(_,_,D),
  D == rnorth -> L = moveforward;
  L = turnright.

shoot_Rwest(L):-
  current(_,_,D),
  D == rwest -> L = shoot;
  L = turnright.

shoot_Reast(L):-
  current(_,_,D),
  D == reast -> L = shoot;
  L = turnright.

shoot_Rsouth(L):-
  current(_,_,D),
  D == rsouth -> L = shoot;
  L = turnright.

shoot_Rnorth(L):-
  current(_,_,D),
  D == rnorth -> L = shoot;
  L = turnright.

random_shoot(L):-
  current(X,Y,_),
  X_W is X-1,   
  X_E is X+1, 
  Y_N is Y+1,  
  Y_S is Y-1,
  (
    (wumpus(X_W,Y), \+wall(X_W,Y_N), \+wall(X_W,Y_S), shoot_Rwest(L));
    (wumpus(X_E,Y), \+wall(X_E,Y_N), \+wall(X_E,Y_S), shoot_Reast(L));
    (wumpus(X,Y_N), \+wall(X_E,Y_N), \+wall(X_W,Y_N), shoot_Rnorth(L));
    (wumpus(X,Y_S), \+wall(X_E,Y_S), \+wall(X_W,Y_S), shoot_Rnorth(L))
  );
  (
    (wumpus(X_W,Y), shoot_Rwest(L));
    (wumpus(X_E,Y), shoot_Reast(L));
    (wumpus(X,Y_N), shoot_Rnorth(L));
    (wumpus(X,Y_S), shoot_Rsouth(L))
  ).

plan(L):-
  current(X,Y,_),
  X_W is X-1, 
  X_E is X+1, 
  Y_N is Y+1, 
  Y_S is Y-1,
  (
    (\+visited(X_W,Y), \+wall(X_W,Y), \+wumpus(X_W,Y), \+confundus(X_W,Y), move_Rwest(L));
    (\+visited(X,Y_S), \+wall(X,Y_S), \+wumpus(X,Y_S), \+confundus(X,Y_S), move_Rsouth(L));
    (\+visited(X_E,Y), \+wall(X_E,Y), \+wumpus(X_E,Y), \+confundus(X_E,Y), move_Reast(L));
    (\+visited(X,Y_N), \+wall(X,Y_N), \+wumpus(X,Y_N), \+confundus(X,Y_N), move_Rnorth(L))
  );
  (
    checkvisited(NewD),
    (
      (NewD == rwest, move_Rwest(L));
      (NewD == reast, move_Reast(L));
      (NewD == rnorth, move_Rnorth(L));
      (NewD == rsouth, move_Rsouth(L))
    )
  ).

danger(L):-
  current(X,Y,_),
  X_W is X-1, 
  X_E is X+1, 
  Y_N is Y+1, 
  Y_S is Y-1,
  (
    wumpusLocated, hasarrow,
    (wumpusLocation(X_W,Y), shoot_Rwest(L));
    (wumpusLocation(X_E,Y), shoot_Reast(L));
    (wumpusLocation(X,Y_N), shoot_Rnorth(L));
    (wumpusLocation(X,Y_S), shoot_Rsouth(L))
  );
  (
    risk, hasarrow, random_shoot(L)
  );
  plan(L).

%% attempt to visit least visited cell
checkvisited(NewD):-
  current(X,Y,_),
  X_W is X-1, 
  X_E is X+1, 
  Y_N is Y+1, 
  Y_S is Y-1,
  (
    ((wall(X_W,Y); confundus(X_W,Y); wumpus(X_W,Y)), Rwestcount = 999999);
    aggregate_all(count, visited(X_W,Y), Rwestcount)
  ),
  (
    ((wall(X_E,Y); confundus(X_E,Y); wumpus(X_E,Y)), Reastcount = 999999);
    aggregate_all(count, visited(X_E,Y), Reastcount)
  ),
  (
    ((wall(X,Y_N); confundus(X,Y_N); wumpus(X,Y_N)), Rnorthcount = 999999);
    aggregate_all(count, visited(X,Y_N), Rnorthcount)
  ),
  (
    ((wall(X,Y_S); confundus(X,Y_S); wumpus(X,Y_S)), Rsouthcount = 999999);
    aggregate_all(count, visited(X,Y_S), Rsouthcount)
  ),
  sort([Rwestcount, Reastcount, Rnorthcount, Rsouthcount], List),
  nth0(0, List, Smallest),
  (
    (Smallest == Rwestcount, NewD = rwest);
    (Smallest == Reastcount, NewD = reast);
    (Smallest == Rnorthcount, NewD = rnorth);
    (Smallest == Rsouthcount, NewD = rsouth)
  ).

