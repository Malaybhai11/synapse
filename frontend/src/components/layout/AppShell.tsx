'use client'

import { AppSidebar } from './AppSidebar'
import { SetupBanner } from './SetupBanner'
import { useImmersiveModeStore } from '@/lib/stores/immersive-mode-store'

interface AppShellProps {
  children: React.ReactNode
}

export function AppShell({ children }: AppShellProps) {
  const { isImmersive } = useImmersiveModeStore()
  
  return (
    <div className="flex h-screen overflow-hidden">
      {!isImmersive && <AppSidebar />}
      <main className="flex-1 flex flex-col min-h-0 overflow-hidden">
        <SetupBanner />
        {children}
      </main>
    </div>
  )
}
