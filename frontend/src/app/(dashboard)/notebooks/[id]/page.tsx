'use client'

import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import { AppShell } from '@/components/layout/AppShell'
import { NotebookHeader } from '../components/NotebookHeader'
import { SourcesColumn } from '../components/SourcesColumn'
import { NotesColumn } from '../components/NotesColumn'
import { ChatColumn } from '../components/ChatColumn'
import { useNotebook } from '@/lib/hooks/use-notebooks'
import { useNotebookSources } from '@/lib/hooks/use-sources'
import { useNotes } from '@/lib/hooks/use-notes'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { useTranslation } from '@/lib/hooks/use-translation'
import { cn } from '@/lib/utils'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { FileText, StickyNote, MessageSquare } from 'lucide-react'

export type ContextMode = 'off' | 'insights' | 'full'

export interface ContextSelections {
  sources: Record<string, ContextMode>
  notes: Record<string, ContextMode>
}

export default function NotebookPage() {
  const { t } = useTranslation()
  const params = useParams()

  // Ensure the notebook ID is properly decoded from URL
  const notebookId = params?.id ? decodeURIComponent(params.id as string) : ''

  const { data: notebook, isLoading: notebookLoading } = useNotebook(notebookId)
  const {
    sources,
    isLoading: sourcesLoading,
    refetch: refetchSources,
    hasNextPage,
    isFetchingNextPage,
    fetchNextPage,
  } = useNotebookSources(notebookId)
  const { data: notes, isLoading: notesLoading } = useNotes(notebookId)

  // Unified tab state (Sources, Notes, or Chat)
  const [activeTab, setActiveTab] = useState<'sources' | 'notes' | 'chat'>('chat')

  // Context selection state
  const [contextSelections, setContextSelections] = useState<ContextSelections>({
    sources: {},
    notes: {}
  })

  // Initialize and update selections when sources load or change
  useEffect(() => {
    if (sources && sources.length > 0) {
      setContextSelections(prev => {
        const newSourceSelections = { ...prev.sources }
        sources.forEach(source => {
          const currentMode = newSourceSelections[source.id]
          const hasInsights = source.insights_count > 0

          if (currentMode === undefined) {
            // Initial setup - default based on insights availability
            newSourceSelections[source.id] = hasInsights ? 'insights' : 'full'
          } else if (currentMode === 'full' && hasInsights) {
            // Source gained insights while in 'full' mode - auto-switch to 'insights'
            newSourceSelections[source.id] = 'insights'
          }
        })
        return { ...prev, sources: newSourceSelections }
      })
    }
  }, [sources])

  useEffect(() => {
    if (notes && notes.length > 0) {
      setContextSelections(prev => {
        const newNoteSelections = { ...prev.notes }
        notes.forEach(note => {
          // Only set default if not already set
          if (!(note.id in newNoteSelections)) {
            // Notes default to 'full'
            newNoteSelections[note.id] = 'full'
          }
        })
        return { ...prev, notes: newNoteSelections }
      })
    }
  }, [notes])

  // Handler to update context selection
  const handleContextModeChange = (itemId: string, mode: ContextMode, type: 'source' | 'note') => {
    setContextSelections(prev => ({
      ...prev,
      [type === 'source' ? 'sources' : 'notes']: {
        ...(type === 'source' ? prev.sources : prev.notes),
        [itemId]: mode
      }
    }))
  }

  if (notebookLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (!notebook) {
    return (
      <AppShell>
        <div className="p-6">
          <h1 className="text-2xl font-bold mb-4">{t.notebooks.notFound}</h1>
          <p className="text-muted-foreground">{t.notebooks.notFoundDesc}</p>
        </div>
      </AppShell>
    )
  }

  return (
    <AppShell>
      <div className="flex flex-col flex-1 min-h-0 bg-background">
        <div className="flex-shrink-0 p-6 pb-2">
          <NotebookHeader notebook={notebook} />
        </div>

        <div className="flex-1 px-6 pb-6 pt-2 overflow-hidden flex flex-col">
          {/* Unified Tabbed Interface */}
          <div className="flex-shrink-0 mb-6">
            <Tabs
              value={activeTab}
              onValueChange={(value) => setActiveTab(value as 'sources' | 'notes' | 'chat')}
              className="w-full"
            >
              <TabsList className="grid w-full grid-cols-3 max-w-2xl mx-auto p-1 bg-muted/30 backdrop-blur-sm border border-border/50 rounded-xl">
                <TabsTrigger
                  value="sources"
                  className={cn(
                    "gap-2 py-2.5 transition-all duration-300 rounded-lg",
                    activeTab === 'sources' && "bg-background text-primary shadow-[0_0_15px_rgba(var(--primary-rgb),0.2)] dark:shadow-[0_0_20px_rgba(var(--primary-rgb),0.3)] ring-1 ring-primary/20"
                  )}
                >
                  <FileText className="h-4 w-4" />
                  <span className="font-medium">{t.navigation.sources}</span>
                </TabsTrigger>
                <TabsTrigger
                  value="notes"
                  className={cn(
                    "gap-2 py-2.5 transition-all duration-300 rounded-lg",
                    activeTab === 'notes' && "bg-background text-primary shadow-[0_0_15px_rgba(var(--primary-rgb),0.2)] dark:shadow-[0_0_20px_rgba(var(--primary-rgb),0.3)] ring-1 ring-primary/20"
                  )}
                >
                  <StickyNote className="h-4 w-4" />
                  <span className="font-medium">{t.common.notes}</span>
                </TabsTrigger>
                <TabsTrigger
                  value="chat"
                  className={cn(
                    "gap-2 py-2.5 transition-all duration-300 rounded-lg",
                    activeTab === 'chat' && "bg-background text-primary shadow-[0_0_15px_rgba(var(--primary-rgb),0.2)] dark:shadow-[0_0_20px_rgba(var(--primary-rgb),0.3)] ring-1 ring-primary/20"
                  )}
                >
                  <MessageSquare className="h-4 w-4" />
                  <span className="font-medium">{t.common.chat}</span>
                </TabsTrigger>
              </TabsList>
            </Tabs>
          </div>

          {/* Active Tab Content */}
          <div className="flex-1 overflow-hidden">
            {activeTab === 'sources' && (
              <div className="h-full animate-in fade-in slide-in-from-bottom-2 duration-300">
                <SourcesColumn
                  sources={sources}
                  isLoading={sourcesLoading}
                  notebookId={notebookId}
                  notebookName={notebook?.name}
                  onRefresh={refetchSources}
                  contextSelections={contextSelections.sources}
                  onContextModeChange={(sourceId, mode) => handleContextModeChange(sourceId, mode, 'source')}
                  hasNextPage={hasNextPage}
                  isFetchingNextPage={isFetchingNextPage}
                  fetchNextPage={fetchNextPage}
                />
              </div>
            )}
            {activeTab === 'notes' && (
              <div className="h-full animate-in fade-in slide-in-from-bottom-2 duration-300">
                <NotesColumn
                  notes={notes}
                  isLoading={notesLoading}
                  notebookId={notebookId}
                  contextSelections={contextSelections.notes}
                  onContextModeChange={(noteId, mode) => handleContextModeChange(noteId, mode, 'note')}
                />
              </div>
            )}
            {activeTab === 'chat' && (
              <div className="h-full animate-in fade-in slide-in-from-bottom-2 duration-300">
                <ChatColumn
                  notebookId={notebookId}
                  contextSelections={contextSelections}
                  sources={sources}
                  sourcesLoading={sourcesLoading}
                />
              </div>
            )}
          </div>
        </div>
      </div>
    </AppShell>
  )
}
