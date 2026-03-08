import { defineStore } from 'pinia';
import { Suit, Rank } from '../types';
import type { GameState, Player, Card, GameStatus } from '../types';

export const useGameStore = defineStore('game', {
  state: (): GameState => ({
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
    initGame() {
      this.status = 'playing';
      this.currentPlayerIndex = 0; // Should be determined by who has 3 of Hearts
      this.lastPlayedCards = [];
      this.lastPlayerIndex = null;
      this.winnerId = null;
      this.setupDeck();
      this.dealCards();
      this.determineFirstPlayer();
    },

    setupDeck() {
      // Create deck according to rules:
      // Remove 3x2, 3xA, 1xK. Total 45 cards.
      // Keep: 1x2, 1xA, 3xK? Wait rules:
      // "Remove 3x2, 3xA, 1xK"
      // Total cards in deck: 52
      // Ranks: 2, 3, 4, 5, 6, 7, 8, 9, 10, J, Q, K, A
      // Suits: S, H, C, D
      
      const allCards: Card[] = [];
      const suits = [Suit.Spades, Suit.Hearts, Suit.Clubs, Suit.Diamonds];
      const ranks = [
        Rank.Three, Rank.Four, Rank.Five, Rank.Six, Rank.Seven, 
        Rank.Eight, Rank.Nine, Rank.Ten, Rank.Jack, Rank.Queen, 
        Rank.King, Rank.Ace, Rank.Two
      ];

      let idCounter = 0;
      
      for (const suit of suits) {
        for (const rank of ranks) {
          // Filter out removed cards
          // Remove 3x2 (Keep only one 2? Which one? Usually Spade 2 is highest, but rules say "2 is biggest single". 
          // Usually in Run Fast with 45 cards:
          // Remove A: Spades, Clubs, Diamonds (Keep Hearts A?) -> Rules just say "Remove 3 As"
          // Remove 2: Spades, Clubs, Diamonds (Keep Hearts 2?) -> Rules just say "Remove 3 2s"
          // Remove K: Any one K.
          // This implies specific suits are removed.
          // Common 15-card Run Fast (3 players):
          // Remove: 
          // 2: Spades, Clubs, Diamonds (Keep Hearts 2? Or usually keep Spades 2? Rules don't specify suit, assume Keep 1)
          // A: Spades, Clubs, Diamonds (Keep Hearts A? Assume Keep 1)
          // K: Remove 1 (e.g. Spades K)
          // But wait, "Remove 3x2, 3xA, 1xK" = 7 cards removed. 52 - 7 = 45. Correct.
          
          // Let's assume we keep the "best" suits or just random?
          // For deterministic gameplay, let's keep:
          // 2: Hearts (or Spades? Usually Spades 2 is biggest in Big 2, but this is Run Fast. Let's keep Spades 2 as the single 2).
          // A: Spades A (Let's keep Spades A).
          // K: Remove Spades K? (Let's keep H, C, D).
          
          let shouldRemove = false;
          
          if (rank === Rank.Two) {
             // Keep Spades 2 only
             if (suit !== Suit.Spades) shouldRemove = true;
          } else if (rank === Rank.Ace) {
             // Keep Spades A only
             if (suit !== Suit.Spades) shouldRemove = true;
          } else if (rank === Rank.King) {
             // Remove Spades K
             if (suit === Suit.Spades) shouldRemove = true;
          }

          if (!shouldRemove) {
            allCards.push({
              suit,
              rank,
              id: `card-${idCounter++}`
            });
          }
        }
      }
      
      // Shuffle
      this.deck = allCards.sort(() => Math.random() - 0.5);
    },

    dealCards() {
      // 3 players, 15 cards each
      const p1Cards = this.deck.slice(0, 15).sort((a, b) => a.rank - b.rank); // Sort for display
      const p2Cards = this.deck.slice(15, 30).sort((a, b) => a.rank - b.rank);
      const p3Cards = this.deck.slice(30, 45).sort((a, b) => a.rank - b.rank);

      this.players = [
        { id: 'human', name: 'You', hand: p1Cards, isHuman: true, score: 0, cardsCount: 15, isTurn: false },
        { id: 'ai-1', name: 'Bot 1', hand: p2Cards, isHuman: false, score: 0, cardsCount: 15, isTurn: false },
        { id: 'ai-2', name: 'Bot 2', hand: p3Cards, isHuman: false, score: 0, cardsCount: 15, isTurn: false },
      ];
    },

    determineFirstPlayer() {
      // Player with 3 of Hearts starts
      // Find who has 3 of Hearts
      let starterIndex = 0;
      this.players.forEach((p, index) => {
        if (p.hand.some(c => c.suit === Suit.Hearts && c.rank === Rank.Three)) {
          starterIndex = index;
        }
      });
      this.currentPlayerIndex = starterIndex;
      this.players[starterIndex].isTurn = true;
    },

    playCards(playerId: string, cards: Card[]) {
      const playerIndex = this.players.findIndex(p => p.id === playerId);
      if (playerIndex === -1) return;

      const player = this.players[playerIndex];
      
      // Remove cards from hand
      player.hand = player.hand.filter(c => !cards.some(played => played.id === c.id));
      player.cardsCount = player.hand.length;
      
      this.lastPlayedCards = cards;
      this.lastPlayerIndex = playerIndex;

      // Check win
      if (player.hand.length === 0) {
        this.winnerId = playerId;
        this.status = 'settlement';
        return;
      }

      this.nextTurn();
    },

    passTurn() {
      this.nextTurn();
    },

    nextTurn() {
      this.players[this.currentPlayerIndex].isTurn = false;
      this.currentPlayerIndex = (this.currentPlayerIndex + 1) % 3;
      
      // If loop back to lastPlayerIndex, new round (clears lastPlayedCards)
      if (this.currentPlayerIndex === this.lastPlayerIndex) {
        this.lastPlayedCards = [];
        this.lastPlayerIndex = null;
      }
      
      this.players[this.currentPlayerIndex].isTurn = true;

      // If AI, trigger AI turn
      if (!this.players[this.currentPlayerIndex].isHuman && this.status === 'playing') {
        this.processAiTurn();
      }
    },

    processAiTurn() {
      setTimeout(() => {
        const player = this.players[this.currentPlayerIndex];
        // Simple AI: 
        // 1. If new round (lastPlayedCards empty), play lowest card.
        // 2. If valid move exists (beat last played), play it. (Simplified: just pass for now to test loop, or play random single if single)
        // 3. Else pass.
        
        if (this.lastPlayedCards.length === 0) {
           // Play lowest card
           const cardToPlay = [player.hand[0]];
           this.playCards(player.id, cardToPlay);
        } else {
           // Try to find a higher card if single
           if (this.lastPlayedCards.length === 1) {
              const cardToBeat = this.lastPlayedCards[0];
              const higherCard = player.hand.find(c => c.rank > cardToBeat.rank);
              if (higherCard) {
                 this.playCards(player.id, [higherCard]);
                 return;
              }
           }
           
           // Otherwise pass
           this.passTurn();
        }
      }, 1000);
    }
  }
});
