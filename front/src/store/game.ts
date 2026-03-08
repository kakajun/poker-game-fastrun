import { defineStore } from 'pinia';
import { Suit, Rank } from '../types';
import type { GameState, Player, Card, GameStatus } from '../types';
import { gameApi, type GameStateModel, type CardModel } from '../api/game';

// Adapter helpers
function mapSuit(backendSuit: number): Suit {
  // Backend: 0: Diamond, 1: Club, 2: Heart, 3: Spade
  switch (backendSuit) {
    case 0: return Suit.Diamonds;
    case 1: return Suit.Clubs;
    case 2: return Suit.Hearts;
    case 3: return Suit.Spades;
    default: return Suit.Spades;
  }
}

function mapCard(c: CardModel): Card {
  return {
    rank: c.rank as Rank,
    suit: mapSuit(c.suit),
    id: c.id.toString() // Convert int ID to string for frontend key
  };
}

export const useGameStore = defineStore('game', {
  state: (): GameState & { gameId: string | null } => ({
    gameId: null,
    status: 'lobby',
    players: [],
    currentPlayerIndex: -1,
    lastPlayedCards: [],
    lastPlayerIndex: null,
    deck: [],
    winnerId: null,
  }),

  getters: {
    currentPlayer: (state) => state.players[state.currentPlayerIndex],
    humanPlayer: (state) => state.players.find(p => p.isHuman),
    opponent1: (state) => state.players.find(p => !p.isHuman && p.id === 'ai-1'),
    opponent2: (state) => state.players.find(p => !p.isHuman && p.id === 'ai-2'),
  },

  actions: {
    async initGame() {
      try {
        const state = await gameApi.startGame();
        this.gameId = state.game_id;
        this.syncState(state);

        // If first player is AI, trigger AI
        if (!this.players[this.currentPlayerIndex].isHuman) {
          this.processAiTurn();
        }
      } catch (e) {
        console.error("Failed to start game", e);
      }
    },

    syncState(backendState: GameStateModel) {
      // 1. Status
      this.status = backendState.is_over ? 'settlement' : 'playing';
      this.winnerId = backendState.winner !== -1 ? (backendState.winner === 0 ? 'human' : `ai-${backendState.winner}`) : null;
      this.currentPlayerIndex = backendState.current_player;
      this.lastPlayerIndex = backendState.last_play_player; // If -1 means no one played yet?

      // 2. Last Played Cards
      if (backendState.last_play) {
        this.lastPlayedCards = backendState.last_play.cards.map(mapCard);
      } else {
        this.lastPlayedCards = [];
      }

      // 3. Players
      // Map 0 -> human, 1 -> ai-1, 2 -> ai-2
      const playerIds = ['human', 'ai-1', 'ai-2'];
      const playerNames = ['You', 'Bot 1', 'Bot 2'];

      this.players = backendState.hands.map((hand, index) => {
        const isHuman = index === 0;
        const id = playerIds[index];
        // Don't sort here, use backend order (descending)
        const mappedHand = hand.map(mapCard);

        return {
          id,
          name: playerNames[index],
          hand: mappedHand,
          isHuman,
          score: backendState.scores[index],
          cardsCount: hand.length,
          isTurn: index === backendState.current_player
        };
      });
    },

    async playCards(playerId: string, cards: Card[]) {
      if (!this.gameId) return;

      // Human action
      // Convert cards to IDs
      const cardIds = cards.map(c => parseInt(c.id));

      try {
        const newState = await gameApi.playerAction(this.gameId, cardIds);
        this.syncState(newState);

        // Check if next is AI
        if (!this.players[this.currentPlayerIndex].isHuman && !this.winnerId) {
          this.processAiTurn();
        }
      } catch (e) {
        console.error("Play failed", e);
        // TODO: Show error toast
        alert("Illegal move or server error");
      }
    },

    async passTurn() {
      if (!this.gameId) return;
      // Pass = empty cards
      try {
        const newState = await gameApi.playerAction(this.gameId, []);
        this.syncState(newState);

        if (!this.players[this.currentPlayerIndex].isHuman && !this.winnerId) {
          this.processAiTurn();
        }
      } catch (e) {
        console.error("Pass failed", e);
        alert("Cannot pass (Must beat if possible)");
      }
    },

    async processAiTurn() {
      if (!this.gameId || this.winnerId) return;

      // Delay for visual effect
      setTimeout(async () => {
        try {
          const newState = await gameApi.triggerAi(this.gameId);
          this.syncState(newState);

          // If still AI turn (next player is AI), trigger again
          if (!this.players[this.currentPlayerIndex].isHuman && !this.winnerId) {
            this.processAiTurn();
          }
        } catch (e) {
          console.error("AI failed", e);
        }
      }, 800); // 800ms delay
    }
  }
});
