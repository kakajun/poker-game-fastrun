<script setup lang="ts">
import { computed } from 'vue';
import { Suit, Rank } from '../types';
import type { Card } from '../types';
import { cn } from '../lib/utils';

const props = defineProps<{
  card: Card;
  isSelected?: boolean;
  isSmall?: boolean;
  isHidden?: boolean; // For opponent cards (back of card)
}>();

const emit = defineEmits<{
  (e: 'click'): void;
}>();

// Map card to image file index based on our assumption:
// Suits: S, H, C, D
// Ranks: 3, 4, 5, 6, 7, 8, 9, 10, J, Q, K, A, 2
// This matches the order in store/game.ts
const imageIndex = computed(() => {
  const suitOrder = [Suit.Spades, Suit.Hearts, Suit.Clubs, Suit.Diamonds];
  const rankOrder = [
    Rank.Three, Rank.Four, Rank.Five, Rank.Six, Rank.Seven,
    Rank.Eight, Rank.Nine, Rank.Ten, Rank.Jack, Rank.Queen,
    Rank.King, Rank.Ace, Rank.Two
  ];

  const suitIndex = suitOrder.indexOf(props.card.suit);
  const rankIndex = rankOrder.indexOf(props.card.rank);
  
  // 1-based index
  return suitIndex * 13 + rankIndex + 1;
});

const imageSrc = computed(() => {
  // Use new URL to resolve asset path
  return new URL(`../assets/porerImg/${imageIndex.value}.png`, import.meta.url).href;
});

const backImageSrc = computed(() => {
    // Assuming there's a back image, or we use a color/pattern
    // If no back image, use a placeholder or check if one of the images is a back
    // Usually card backs are not in the 1-52 range.
    // Let's use a CSS background for now.
    return ''; 
});

const handleClick = () => {
  if (!props.isHidden) {
    emit('click');
  }
};
</script>

<template>
  <div 
    class="relative transition-transform duration-200 select-none"
    :class="cn(
      'cursor-pointer hover:-translate-y-2',
      isSelected ? '-translate-y-6' : '',
      isSmall ? 'w-16 h-24' : 'w-24 h-36', // Standard size vs small size
      isHidden ? 'bg-blue-800 border-2 border-white rounded-lg' : ''
    )"
    @click="handleClick"
  >
    <img 
      v-if="!isHidden"
      :src="imageSrc" 
      :alt="`${card.suit}${card.rank}`"
      class="w-full h-full object-contain drop-shadow-md"
      draggable="false"
    />
    <div v-else class="w-full h-full flex items-center justify-center text-white">
       <!-- Card Back Pattern -->
       <div class="w-full h-full bg-gradient-to-br from-blue-600 to-blue-900 rounded-lg border border-blue-400"></div>
    </div>
  </div>
</template>
