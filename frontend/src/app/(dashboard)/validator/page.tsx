'use client'

import { useState } from 'react'
import { AppShell } from '@/components/layout/AppShell'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Textarea } from '@/components/ui/textarea'
import { Button } from '@/components/ui/button'
import { useValidator } from '@/lib/hooks/use-validator'
import { useModelDefaults, useModels } from '@/lib/hooks/use-models'
import { AdvancedModelsDialog } from '@/components/search/AdvancedModelsDialog'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { ValidatorReport } from '@/components/validator/ValidatorReport'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { SourceType } from '@/lib/types/validator'
import { cn } from '@/lib/utils'
import {
  FileText,
  BarChart3,
  ShieldAlert,
  Settings,
  AlertCircle,
  Play,
  Globe,
  BookOpen,
  Layers,
} from 'lucide-react'

const SOURCE_OPTIONS: { value: SourceType; label: string; icon: React.ReactNode; description: string }[] = [
  {
    value: 'notebook',
    label: 'Knowledge Base',
    icon: <BookOpen className="h-5 w-5" />,
    description: 'Critique using your saved notes & sources',
  },
  {
    value: 'web',
    label: 'Web Search',
    icon: <Globe className="h-5 w-5" />,
    description: 'Red-team using live web data',
  },
  {
    value: 'both',
    label: 'Hybrid (Both)',
    icon: <Layers className="h-5 w-5" />,
    description: 'Most thorough attack surface',
  },
]

export default function ValidatorPage() {
  const [idea, setIdea]           = useState('')
  const [sourceType, setSourceType] = useState<SourceType>('both')
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [customModels, setCustomModels] = useState<{
    strategy: string; answer: string; finalAnswer: string
  } | null>(null)
  const [activeTab, setActiveTab] = useState<'input' | 'result'>('input')

  const { data: modelDefaults } = useModelDefaults()
  const { data: availableModels } = useModels()
  const { runValidator, data, isPending, isError, error } = useValidator()

  const modelNameById = new Map(availableModels?.map(m => [m.id, m.name]) || [])
  const resolveName = (id?: string | null) =>
    id ? (modelNameById.get(id) ?? id) : 'Not set'

  const handleRun = () => {
    if (!idea.trim() || !modelDefaults?.default_chat_model) return
    const models = customModels || {
      strategy:   modelDefaults.default_chat_model,
      answer:     modelDefaults.default_chat_model,
      finalAnswer: modelDefaults.default_chat_model,
    }
    runValidator(
      {
        idea,
        sourceType,
        models: {
          analyzerModel:   models.strategy,
          redTeamModel:    models.answer,
          strategistModel: models.finalAnswer,
        },
      },
      { onSuccess: () => setActiveTab('result') }
    )
  }

  return (
    <AppShell>
      <div className="flex flex-col h-full bg-background overflow-hidden font-sans">

        {/* Header + Tabs */}
        <div className="flex-shrink-0 p-6 pb-2">
          <div className="flex items-center gap-3 mb-6">
            <ShieldAlert className="h-8 w-8 text-primary" />
            <h1 className="text-xl md:text-3xl font-bold tracking-tight">Critique Mode</h1>
            <Badge variant="outline" className="ml-2 text-xs border-primary/30 text-primary bg-primary/5">
              Devil's Advocate
            </Badge>
          </div>

          <Tabs
            value={activeTab}
            onValueChange={(v) => setActiveTab(v as 'input' | 'result')}
            className="w-full"
          >
            <TabsList className="grid w-full grid-cols-2 p-1 bg-muted/30 backdrop-blur-sm border border-border/50 rounded-xl">
              <TabsTrigger
                value="input"
                className={cn(
                  'gap-2 py-2.5 transition-all duration-300 rounded-lg',
                  activeTab === 'input' &&
                    'bg-background text-primary shadow-[0_0_15px_rgba(var(--primary-rgb),0.2)] dark:shadow-[0_0_20px_rgba(var(--primary-rgb),0.3)] ring-1 ring-primary/20'
                )}
              >
                <FileText className="h-4 w-4" />
                <span className="font-medium">Setup &amp; Run</span>
              </TabsTrigger>
              <TabsTrigger
                value="result"
                disabled={!data && !isPending}
                className={cn(
                  'gap-2 py-2.5 transition-all duration-300 rounded-lg',
                  activeTab === 'result' &&
                    'bg-background text-primary shadow-[0_0_15px_rgba(var(--primary-rgb),0.2)] dark:shadow-[0_0_20px_rgba(var(--primary-rgb),0.3)] ring-1 ring-primary/20'
                )}
              >
                {isPending ? <LoadingSpinner size="sm" /> : <BarChart3 className="h-4 w-4" />}
                <span className="font-medium">Critique Report</span>
              </TabsTrigger>
            </TabsList>
          </Tabs>
        </div>

        {/* Content */}
        <div className="flex-1 px-6 pb-6 pt-2 overflow-y-auto min-h-0 custom-scrollbar">
          <div className="max-w-6xl mx-auto">

            {/* ── SETUP TAB ── */}
            {activeTab === 'input' && (
              <div className="animate-in fade-in slide-in-from-bottom-2 duration-300 space-y-6">

                {/* Idea Input Card */}
                <Card className="border-2 border-primary/10 shadow-lg overflow-hidden">
                  <CardHeader className="bg-muted/30 pb-4">
                    <CardTitle className="text-xl flex items-center gap-2">
                      <ShieldAlert className="h-5 w-5 text-primary" /> Submit Your Idea or Plan
                    </CardTitle>
                    <CardDescription>
                      Describe your idea, plan, or architecture. Three AI agents will systematically attack every assumption to surface hidden risks.
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="pt-6 space-y-6">

                    {/* Textarea */}
                    <div className="space-y-3">
                      <Label htmlFor="idea-input" className="text-base font-semibold">Your Idea or Plan</Label>
                      <Textarea
                        id="idea-input"
                        placeholder="e.g. I want to launch a SaaS product for freelancers that automatically tracks time and generates invoices using AI..."
                        value={idea}
                        onChange={(e) => setIdea(e.target.value)}
                        className="resize-none text-base min-h-[160px] border-primary/20 focus-visible:ring-primary rounded-xl"
                        onKeyDown={(e) => {
                          if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
                            e.preventDefault()
                            handleRun()
                          }
                        }}
                      />
                      <div className="flex justify-between items-center text-xs text-muted-foreground bg-muted/20 p-2 rounded-lg border border-border/50">
                        <span className="flex items-center gap-1.5">
                          <AlertCircle className="h-3 w-3" /> Be detailed — more context = better attack surface
                        </span>
                        <span>Press <kbd className="px-1.5 py-0.5 rounded border bg-background font-sans text-[10px]">Cmd/Ctrl+Enter</kbd> to run</span>
                      </div>
                    </div>

                    {/* Source Selector */}
                    <div className="space-y-3">
                      <Label className="text-base font-semibold">Research Source</Label>
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                        {SOURCE_OPTIONS.map((opt) => (
                          <button
                            key={opt.value}
                            type="button"
                            onClick={() => setSourceType(opt.value)}
                            className={cn(
                              'flex flex-col items-start gap-2 p-4 rounded-xl border-2 text-left transition-all duration-200 hover:border-primary/40 hover:bg-primary/5',
                              sourceType === opt.value
                                ? 'border-primary bg-primary/10 shadow-md shadow-primary/10 ring-1 ring-primary/20'
                                : 'border-border bg-card hover:shadow-sm'
                            )}
                          >
                            <span className={cn('', sourceType === opt.value ? 'text-primary' : 'text-muted-foreground')}>
                              {opt.icon}
                            </span>
                            <span className={cn('text-sm font-semibold', sourceType === opt.value ? 'text-primary' : '')}>
                              {opt.label}
                            </span>
                            <span className="text-xs text-muted-foreground leading-snug">{opt.description}</span>
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Model Config Row */}
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-2xl border bg-card/50 backdrop-blur-sm shadow-sm">
                      <div className="flex gap-2 text-[10px] flex-wrap items-center">
                        <span className="text-muted-foreground font-medium uppercase tracking-wider mr-1">Agents:</span>
                        <Badge variant="outline" className="opacity-90 bg-primary/5 border-primary/20 px-2 py-0">
                          Analyzer: {resolveName(customModels?.strategy || modelDefaults?.default_chat_model)}
                        </Badge>
                        <Badge variant="outline" className="opacity-90 bg-rose-500/5 border-rose-500/20 text-rose-600 px-2 py-0">
                          Red Team: {resolveName(customModels?.answer || modelDefaults?.default_chat_model)}
                        </Badge>
                        <Badge variant="outline" className="opacity-90 bg-primary/5 border-primary/20 px-2 py-0">
                          Strategist: {resolveName(customModels?.finalAnswer || modelDefaults?.default_chat_model)}
                        </Badge>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setShowAdvanced(true)}
                        className="h-8 py-1 px-3 border border-border/50 hover:bg-muted rounded-lg shrink-0"
                      >
                        <Settings className="h-3.5 w-3.5 mr-2" /> Configure
                      </Button>
                    </div>

                    {/* Run Button */}
                    <Button
                      size="lg"
                      className="w-full text-base h-14 rounded-2xl shadow-lg shadow-primary/20 transition-all hover:shadow-primary/30 active:scale-[0.98]"
                      onClick={handleRun}
                      disabled={isPending || !idea.trim()}
                    >
                      {isPending ? (
                        <>
                          <LoadingSpinner size="sm" className="mr-3" />
                          Red Team In Progress...
                        </>
                      ) : (
                        <>
                          <Play className="h-5 w-5 mr-3 fill-current" />
                          Run Critique Engine
                        </>
                      )}
                    </Button>

                    {isError && (
                      <div className="p-4 bg-destructive/10 text-destructive rounded-xl border border-destructive/20 flex items-start gap-4 animate-in shake duration-500">
                        <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" />
                        <div>
                          <h4 className="font-bold">Error running critique</h4>
                          <p className="text-sm opacity-90 leading-snug">{error?.message || 'An unknown error occurred'}</p>
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>
            )}

            {/* ── RESULT TAB ── */}
            {activeTab === 'result' && (
              <div className="animate-in fade-in slide-in-from-bottom-2 duration-300 pb-12">
                {isPending ? (
                  <div className="flex flex-col items-center justify-center py-32 space-y-6">
                    <div className="relative">
                      <LoadingSpinner size="lg" className="h-16 w-16" />
                      <ShieldAlert className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-6 w-6 text-primary animate-pulse" />
                    </div>
                    <div className="text-center space-y-2">
                      <p className="text-xl font-bold tracking-tight">Red Team Active</p>
                      <p className="text-muted-foreground text-sm max-w-xs mx-auto">
                        Unpacking assumptions, probing vulnerabilities, and formulating mitigations...
                      </p>
                    </div>
                  </div>
                ) : data ? (
                  <ValidatorReport data={data} />
                ) : (
                  <div className="flex flex-col items-center justify-center py-32 text-muted-foreground">
                    <ShieldAlert className="h-16 w-16 opacity-10 mb-6" />
                    <p className="font-medium">Submit an idea to see the critique report here.</p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        <AdvancedModelsDialog
          open={showAdvanced}
          onOpenChange={setShowAdvanced}
          defaultModels={{
            strategy:   customModels?.strategy    || modelDefaults?.default_chat_model || '',
            answer:     customModels?.answer      || modelDefaults?.default_chat_model || '',
            finalAnswer: customModels?.finalAnswer || modelDefaults?.default_chat_model || '',
          }}
          onSave={setCustomModels}
        />
      </div>
    </AppShell>
  )
}
