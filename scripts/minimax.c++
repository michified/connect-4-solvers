#include <chrono>
#include <string>
#include <cstring>
#include <iostream>
#include <map> 
#include <thread>

// optimization flags for the compiler for higher efficiency (i am not convinced that they actually help though)
#pragma GCC optimize("O3")
#pragma GCC optimize("Ofast,unroll-loops")

#define ll long long
using namespace std;
using ms = chrono::duration<double, milli>;

const int height = 6, width = 7;
const int bitwiseDirs[4] = {1, 7, 8, 6}; // bitwise shift constants for vertical, horizontal, and diagonal movement
const int order[7] = {3, 2, 4, 5, 1, 0, 6}; // the order in which the bot checks columns
const int cmpChain[10] = {0, 0, 0, 0, 100, 1000, 10000, 100000, 10000001, 10000001};
const int hmnChain[10] = {0, 0, 0, 0, -101, -1010, -10001, -100010, -10000000, -10000000};
int parity;

class BoardState {
private:
	int player; // player is -1, machine is 1
	int board[height][width];
	// turns columns into implicit, random-accessible stacks (as is the nature of the connect 4 columns)
	// allows the current height of the column to be instantly obtained instead of looping through each row (O(1) instead of O(H))
	// results in a ~7x speedup when adding/removing pieces from columns as H = 7
	int numPieces[width];
	ll cmpBitBoard;
	ll hmnBitBoard;
	/* 
	0s and 1s to track which positions have pieces of each side
	bit powers correspond to the grid:
	5 12 19 26 33 40 47
	4 11 18 25 32 39 46
	3 10 17 24 31 38 45
	2 9  16 23 30 37 44
	1 8  15 22 29 36 43
	0 7  14 21 28 35 42
	there is a row skipped at the top to ensure that there are no false wins when checking
	more specifically to prevent things like 4 5 7 8 to be counted as a win
	*/ 

	// checks if the coordinates are inside the grid
	bool valid(int row, int col) {
		return row >= 0 and row < height and col >= 0 and col < width;
	}

	bool change(int val, int& cmpcnt, int& hmncnt, int& nthcnt, int by) { // true if nthcnt was changed
		if (val == 1) {
			cmpcnt += by;
			return false;
		}
		if (val == -1) {
			hmncnt += by;
			return false;
		}
		nthcnt += by;
		return true;
	}

	// sliding window computations improve performance by x4
	int evalLine(int srow, int scol, int drow, int dcol) {
		int cmpcnt = 0, hmncnt = 0, nthcnt = 0, eval = 0, lrow, lcol, rrow, rcol, i, goodParityCnt = 0;

		if (not valid(srow + drow * 3, scol + dcol * 3)) return 0;

		lrow = rrow = srow;
		lcol = rcol = scol;
		for (i = 0; i <= 3; i++) {
			if (change(board[rrow][rcol], cmpcnt, hmncnt, nthcnt, 1)) {
				if (rcol % 2 == parity) goodParityCnt++;
			}
			rrow += drow;
			rcol += dcol;
		}

		if (hmncnt == 0 and nthcnt == 4 - cmpcnt) eval += cmpChain[cmpcnt * 2 + (goodParityCnt == nthcnt)];
		else if (cmpcnt == 0 and nthcnt == 4 - hmncnt) eval += hmnChain[hmncnt * 2 + (goodParityCnt == 0)];
		
		while (valid(rrow, rcol)) {
			if (change(board[lrow][lcol], cmpcnt, hmncnt, nthcnt, -1)) {
				if (rcol % 2 == parity) goodParityCnt--;
			}
			lrow += drow;
			lcol += dcol;
			if (change(board[rrow][rcol], cmpcnt, hmncnt, nthcnt, 1)) {
				if (rcol % 2 == parity) goodParityCnt++;
			}
			rrow += drow;
			rcol += dcol;

			if (hmncnt == 0 and nthcnt == 4 - cmpcnt) eval += cmpChain[cmpcnt * 2 + (goodParityCnt == nthcnt)];
			else if (cmpcnt == 0 and nthcnt == 4 - hmncnt) eval += hmnChain[hmncnt * 2 + (goodParityCnt == 0)];
		}

		return eval;
	}

public:
	// constructor
	BoardState(int player) {
		this->player = player;
		memset(board, 0, sizeof(board));
		memset(numPieces, 0, sizeof(numPieces));
		cmpBitBoard = 0;
		hmnBitBoard = 0;
	}

	// accessor and mutator methods
	int getPlayer() {
		return player;
	}

	void flipPlayer() {
		player = -player;
	}

	bool canAdd(int col) {
		return numPieces[col] < height;
	}

	void addToCol(int col) {
		board[numPieces[col]][col] = player;
		if (player == 1) cmpBitBoard ^= 1ll << (col * 7 + numPieces[col]);
		else hmnBitBoard ^= 1ll << (col * 7 + numPieces[col]);
		numPieces[col]++;
	}

	void removeFromCol(int col) {
		numPieces[col]--;
		if (player == 1) cmpBitBoard ^= 1ll << (col * 7 + numPieces[col]);
		else hmnBitBoard ^= 1ll << (col * 7 + numPieces[col]);
		board[numPieces[col]][col] = 0;
	}

	pair<ll, ll> getBitBoards() {
		return {cmpBitBoard, hmnBitBoard};
	}

	// uses the bitboards to quickly determine whether someone won (O(1) instead of O(WH)) 
	// results in an ~100x speedup during checking for wins
	int isWin() {
        for (int direction : bitwiseDirs) {
            ll bb = cmpBitBoard;
            if ((bb & (bb >> direction) & (bb >> (direction * 2)) & (bb >> (direction * 3))) != 0) return 1;
        }
        for (int direction : bitwiseDirs) {
            ll bb = hmnBitBoard;
            if ((bb & (bb >> direction) & (bb >> (direction * 2)) & (bb >> (direction * 3))) != 0) return -1;
        }
        return 0;
    }

	// function that takes a player and calculates their score; higher means more advantageous for the player
	int staticEval() {
		int i, j, eval = 0;
		
		for (i = 0; i < height; i++) eval += evalLine(i, 0, 0, 1); // rows
		
		for (j = 0; j < width; j++) eval += evalLine(numPieces[j] == height ? 0 : numPieces[j], j, -1, 0); // columns

		// '/' diagonals
		for (i = 1; i <= 2; i++) eval += evalLine(i, 0, 1, 1);
		for (j = 0; j <= 3; j++) eval += evalLine(0, j, 1, 1);

		// '\' diagonals
		for (j = 3; j < width; j++) eval += evalLine(0, j, 1, -1);
		for (i = 1; i <= 2; i++) eval += evalLine(i, width - 1, 1, -1);

		return eval;
	}

	void printBoard() {
		int row, col;
		for (int i = 1; i <= width; i++) cout << i << ' ';
		cout << endl;

		for (row = height - 1; row >= 0; row--) {
			for (col = 0; col < width; col++) {
				if (board[row][col] == 1) cout << "O ";
				else if (board[row][col] == -1) cout << "X ";
				else cout << "_ ";
			}
			cout << endl;
		}
	}
};

/*
transposition tables are
a dynamic programming approach to reduce recomputations by storing the bitboard : result as key-value pairs to avoid 
processing the same subtree again; however, maps (binary search trees) introduce an extra log factor
seenTTable stores the best moves calculated during previous turns to suggest columns to search first as alpha-beta 
search prunes away suboptimal branches faster when encountering a near-optimal branch first
results in an ~8x speedup from testing
first.first: evalVal, first.second: bestChoice, second: depth
*/
map<pair<ll, ll>, pair<pair<int, int>, int>> trnspTable, seenTTable;

/*
the minimax algorithm is the central idea that allows computers to exhaust positions and find optimal moves
it assumes that the computer tries to maximize the score of the board while the player tries to minimize it
*/
pair<int, int> minimax(BoardState& state, int alpha, int beta, int depth) {
	// checks wheter this board has been calculated before
	if (trnspTable.find(state.getBitBoards()) != trnspTable.end() and trnspTable[state.getBitBoards()].second >= depth) {
        return trnspTable[state.getBitBoards()].first;
    }

	// (base case) checks whether the depth limit has been reached or someone has won already
	int eval = state.isWin();
	if (eval == 1) return {cmpChain[9], 0};
	else if (eval == -1) return {hmnChain[9], 0};
	if (depth == 0) return {state.staticEval(), 0};

	int best = -1, bestEval;
	if (state.getPlayer() == 1) bestEval = INT_MIN;
	else bestEval = INT_MAX;

	// best is set to the closest non-full row to the center
	for (int col : order) {
		if (state.canAdd(col)) {
			best = col;
			break;
		}
	}

	/*
	checks the children of the current node of the game tree in descending order of predicted score
	before this, it checks the best move suggested by searches done in previous turns
	by searching in this fashion, the alpha-beta concept can prune away suboptimal branches quicker, which
	results in a ~50x speedup from testing
	*/
	int toSearch = 3;
	if (seenTTable.find(state.getBitBoards()) != seenTTable.end()) toSearch = seenTTable[state.getBitBoards()].first.second;

	if (state.canAdd(toSearch)) {
		state.addToCol(toSearch);
		state.flipPlayer();
		eval = minimax(state, alpha, beta, depth - 1).first;
		state.flipPlayer();
		state.removeFromCol(toSearch);
		
		if (state.getPlayer() == 1) {
			if (eval > bestEval) {
				bestEval = eval;
				best = toSearch;
			}
			alpha = max(alpha, eval);
		} else {
			if (eval < bestEval) {
				bestEval = eval;
				best = toSearch;
			}
			beta = min(beta, eval);
		}

		if (beta <= alpha) {
			trnspTable[state.getBitBoards()] = {{bestEval, best}, depth};
			return {bestEval, best};
		}
	}

	for (int col : order) {
		if (not state.canAdd(col) or col == toSearch) continue;

		state.addToCol(col);
		state.flipPlayer();
		eval = minimax(state, alpha, beta, depth - 1).first;
		state.flipPlayer();
		state.removeFromCol(col);
		
		if (state.getPlayer() == 1) {
			if (eval > bestEval) {
				bestEval = eval;
				best = col;
			}
			alpha = max(alpha, eval);
		} else {
			if (eval < bestEval) {
				bestEval = eval;
				best = col;
			}
			beta = min(beta, eval);
		}

		if (beta <= alpha) break;
	}

	// stores this state in the transposition table to be used later (potentially)
	if (trnspTable.find(state.getBitBoards()) == trnspTable.end() or trnspTable[state.getBitBoards()].second < depth) {
        trnspTable[state.getBitBoards()] = {{bestEval, best}, depth};
    }
	return {bestEval, best};
}

int allowedMS = 2500;

int main() {
	int starting, col, movesLeft = width * height;
	char inp;
	cout << "Do you want to start first? Type 'y' if you do, otherwise type 'n'." << endl;
	cin >> inp;
	if (inp == 'y') {
		starting = -1;
		parity = 1;
	} else {
		starting = 1;
		parity = 0;
	}

	cout << "Around how many milliseconds should the computer be allowed to think? (minimum: 4000ms, the computer may go over this amount slightly)" << endl;
	string inpMS;
	cin >> inpMS;
	while (inpMS.find_first_not_of("0123456789") != string::npos or inpMS.empty()) {
		cout << "Invalid input! Please enter a number." << endl;
		cin >> inpMS;
	}
	int intinpMS = stoi(inpMS);
	if (intinpMS < 4000) {
		cout << "Invalid input! Defaulting to 4000ms." << endl;
	} else {
		allowedMS = intinpMS;
	}

	this_thread::sleep_for(chrono::milliseconds(2000));

	BoardState state(starting);

	while (movesLeft--) {
		state.printBoard();

		if (state.getPlayer() == -1) {
			cout << "Your turn! Which column?" << endl;
			cin >> inp;
			col = inp - '0' - 1;
			while (col < 0 or col >= width or not state.canAdd(col)) {
				cout << "Invalid column! Please try again." << endl;
				cin >> inp;
				col = inp - '0' - 1;
			}
			cout << "Piece placed in column " << col + 1 << "." << endl << endl;
		} else {
			cout << "Computer is thinking..." << endl;
			const auto before = chrono::system_clock::now();
			ms totalElapsed;
			int allowedDepth = 1;
			if (movesLeft == 1) {
				for (col = 0; col < width; col++) {
					if (state.canAdd(col)) break;
				}
				totalElapsed = chrono::system_clock::now() - before;
			} else {
				for (auto& elem : trnspTable) {
					if (seenTTable.find(elem.first) == seenTTable.end() or
						seenTTable[elem.first].second < elem.second.second) seenTTable[elem.first] = elem.second;
				}
				trnspTable.clear();
				col = minimax(state, INT_MIN, INT_MAX, allowedDepth).second;
				totalElapsed = chrono::system_clock::now() - before;

				/*
				this is the concept of iterative deepening depth-first search (IDDFS)
				allows DFS to go deeper and deeper if time allows
				which may actually be faster than just directly searching at the most optimal depth (which is hard to predict too)
				when combined with transposition tables
				a timer is also kept to prevent the search for taking too long; the timeout value can be modified
				*/
				pair<int, int> tmp;
				while (totalElapsed.count() < allowedMS and allowedDepth < movesLeft) {
					for (auto& elem : trnspTable) {
						if (seenTTable.find(elem.first) == seenTTable.end() or
							seenTTable[elem.first].second < elem.second.second) seenTTable[elem.first] = elem.second;
					}
					trnspTable.clear();
					allowedDepth++;
					const auto before2 = chrono::system_clock::now();
					col = minimax(state, INT_MIN, INT_MAX, allowedDepth).second;
					totalElapsed = chrono::system_clock::now() - before;
				}
			}
			cout << "Piece placed in column " << col + 1 << ". (Depth: " << allowedDepth << ") (" << totalElapsed.count() << "ms)"<< endl << endl;
		}

		state.addToCol(col);

		if (abs(state.isWin()) == 1) {
			state.printBoard();
			if (state.getPlayer() == 1) cout << "Computer wins.";
			else cout << "You win.";
			return 0;
		}

		state.flipPlayer();
	}

	state.printBoard();
	cout << "Tie!";
	return 0;
}

/*
overall, with the addition of the aforementioned optimization techniques, the program can search up to depth 14
in the first few moves of the game, which is a (W = 7)^(D = 6) = ~100,000x speedup compared to a naive method that can 
only search up to a depth of 8 when both are halted after 3 seconds

note: when the computer takes less than 3 seconds to make a move, it usually means that the computer has
'solved' the position: it found a strategy to win no matter what the player plays
*/