import { create } from 'zustand'

interface ImmersiveModeState {
  isImmersive: boolean
  toggleImmersive: () => void
  setImmersive: (immersive: boolean) => void
}

export const useImmersiveModeStore = create<ImmersiveModeState>((set) => ({
  isImmersive: false,
  toggleImmersive: () => set((state) => ({ isImmersive: !state.isImmersive })),
  setImmersive: (immersive) => set({ isImmersive: immersive }),
}))
