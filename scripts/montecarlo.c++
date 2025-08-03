#include <vector>
#include <chrono>
#include <cmath>
#include <algorithm>
#include <cstring>
#include <string>
#pragma GCC optimize("O3")
#pragma GCC optimize("Ofast,unroll-loops")
#define ll long long
using namespace std;
using ms = chrono::duration<double, milli>;

const int height = 6, width = 7;
const int bitwiseDirs[4] = {1, 7, 8, 6}; // bitwise shift constants for vertical, horizontal, and diagonal movement

class BoardState {
public:
	int player; // player is -1, machine is 1
	int numPieces[width];
	int placed;
	ll cmpBitBoard;
	ll hmnBitBoard;
	double wins;
	double total;
	int ptr;
	vector<BoardState*> children;

	BoardState(ll cmpBitBoard, ll hmnBitBoard) { // create new instance
		player = -1;
		placed = 0;
		memset(numPieces, 0, sizeof(numPieces));
		for (ll row = 1 << (height - 1); row >= 1; row >>= 1) {
			int col = 0;
			for (ll cell = row; cell <= (1ll << 47); cell <<= 7) {
				if ((cmpBitBoard & cell) or (hmnBitBoard & cell)) {
					numPieces[col]++; 
					placed++;
				}
				col++;
			}
		}
		this->cmpBitBoard = cmpBitBoard;
		this->hmnBitBoard = hmnBitBoard;
		wins = 0;
		total = 0.00001;
	}

	BoardState(BoardState* toClone, int move) { // creates instance of next move
		for (int i = 0; i < width; i++) numPieces[i] = toClone->numPieces[i];
		placed = toClone->placed;
		cmpBitBoard = toClone->cmpBitBoard;
		hmnBitBoard = toClone->hmnBitBoard;
		player = -toClone->player;
		addToCol(move);
		wins = 0;
		total = 0.00001;
		ptr = 0;
	}

	BoardState(BoardState* toClone) { // clones current instance
		player = toClone->player;
		for (int i = 0; i < width; i++) numPieces[i] = toClone->numPieces[i];
		cmpBitBoard = toClone->cmpBitBoard;
		hmnBitBoard = toClone->hmnBitBoard;
		wins = 0;
		total = 0;
		placed = toClone->placed;
		ptr = 0;
	}	

	bool canAdd(int col) {
		return numPieces[col] < height;
	}

	void addToCol(int col) {
		if (player == 1) cmpBitBoard ^= 1ll << (col * 7 + numPieces[col]);
		else hmnBitBoard ^= 1ll << (col * 7 + numPieces[col]);
		numPieces[col]++;
		placed++;
	}

	int isWin() {
		for (int direction : bitwiseDirs) {
			if ((cmpBitBoard & (cmpBitBoard >> direction) & (cmpBitBoard >> (direction * 2)) & (cmpBitBoard >> (direction * 3))) != 0) return 1;
		}
		for (int direction : bitwiseDirs) {
			if ((hmnBitBoard & (hmnBitBoard >> direction) & (hmnBitBoard >> (direction * 2)) & (hmnBitBoard >> (direction * 3))) != 0) return -1;
		}
		return 0;
	}
};

double c = sqrt(2);

double uct(BoardState* board, int curRan) {
	return board->wins / board->total + c * sqrt(log(curRan + 1) / board->total);
}

void traverse(vector<BoardState*>& path) {
	while (not path.back()->children.empty() and path.back()->ptr == width and not path.back()->isWin()) {
		double bestUCT = -1, res;
		BoardState* best;
		for (auto child : path.back()->children) {
			res = uct(child, path.back()->total);
			if (res > bestUCT) {
				bestUCT = res;
				best = child;
			}
		}
		path.push_back(best);
	}
}

int rollout(BoardState* board) {
	BoardState copy(board);
	int move, played = copy.placed;
	while (not copy.isWin() and played < width * height) {
		move = rand() % width;
		while (not copy.canAdd(move)) move = rand() % width;
		copy.addToCol(move);
		copy.player = -copy.player;
		played++;
	}
	return copy.isWin();
}

void monteCarlo(BoardState* board) {
	vector<BoardState*> path = {board};
	traverse(path);
	int verdict;
	if (path.back()->placed == width * height or path.back()->isWin()) {
		verdict = path.back()->isWin();
		path.back()->ptr = width;
	} else if (path.back()->total == 0) {
		verdict = rollout(path.back());
	} else {
		while (path.back()->ptr < width) {
			if (path.back()->canAdd(path.back()->ptr)) {
				path.back()->children.push_back(new BoardState(path.back(), path.back()->ptr));
				path.back()->ptr++;
				break;
			}
			path.back()->ptr++;
		}
		auto cur = path.back()->children.back();
		if (not cur->isWin()) verdict = rollout(cur);
		else verdict = cur->isWin();
		cur->total++;
		if (cur->player == verdict) cur->wins++;
		else if (verdict == 0) cur->wins += 0.5;
	}
	for (auto node : path) {
		node->total++;
		if (node->player == verdict) node->wins++;
		else if (verdict == 0) node->wins += 0.5;
	}
}

int allowedMS;

int main(int argc, char** argv) {
	int col;

	BoardState state(stoll(argv[1]), stoll(argv[2])), dummy(0ll, 0ll);
	allowedMS = stoi(argv[3]);

	const auto before = chrono::system_clock::now();
	ms totalElapsed = chrono::system_clock::now() - before;
	dummy.children.push_back(new BoardState(state));
	dummy.children.back()->ptr = width;
	for (int i = 0; i < width; i++) {
		if (dummy.children[0]->canAdd(i)) dummy.children[0]->children.push_back(new BoardState(dummy.children[0], i));
	}
	while (totalElapsed.count() < allowedMS) {
		monteCarlo(dummy.children[0]);
		totalElapsed = chrono::system_clock::now() - before;
	}
	double best = 0;
	int cur = 0;
	for (int i = 0; i < width; i++) {
		if (not dummy.children[0]->canAdd(i)) continue;
		auto child = dummy.children[0]->children[cur];
		cur++;
		if (child->total > best) {
			best = child->total;
			col = i;
		}
	}
	return col;
}