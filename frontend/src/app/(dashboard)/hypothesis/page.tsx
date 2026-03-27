'use client'

import { useState } from 'react'
import { useTranslation } from '@/lib/hooks/use-translation'
import { AppShell } from '@/components/layout/AppShell'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Badge } from '@/components/ui/badge'
import { Textarea } from '@/components/ui/textarea'
import { Button } from '@/components/ui/button'
import { HypothesisReport } from '@/components/hypothesis/HypothesisReport'
import { useHypothesis } from '@/lib/hooks/use-hypothesis'
import { useModelDefaults, useModels } from '@/lib/hooks/use-models'
import { AdvancedModelsDialog } from '@/components/search/AdvancedModelsDialog'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { FileText, BarChart3, Scale, Settings, AlertCircle, Play, Globe } from 'lucide-react'
import { cn } from '@/lib/utils'

export default function HypothesisPage() {
  const { t } = useTranslation()
  const [hypothesis, setHypothesis] = useState('')
  const [includeWebSearch, setIncludeWebSearch] = useState(false)
  const [showAdvancedModels, setShowAdvancedModels] = useState(false)
  const [customModels, setCustomModels] = useState<{
    strategy: string
    answer: string
    finalAnswer: string
  } | null>(null)

  const { data: modelDefaults, isLoading: modelsLoading } = useModelDefaults()
  const { data: availableModels } = useModels()
  const { evaluateHypothesis, data, isPending, isError, error } = useHypothesis()
  const [activeTab, setActiveTab] = useState<'input' | 'result'>('input')

  const modelNameById = new Map(availableModels?.map((model) => [model.id, model.name]) || [])
  const resolveModelName = (id?: string | null) => {
    if (!id) return t.searchPage?.notSet || "Not set"
    return modelNameById.get(id) ?? id
  }

  const handleRunHypothesis = () => {
    if (!hypothesis.trim() || !modelDefaults?.default_chat_model) return

    const models = customModels || {
      strategy: modelDefaults.default_chat_model,
      answer: modelDefaults.default_chat_model,
      finalAnswer: modelDefaults.default_chat_model
    }

    evaluateHypothesis({
      query: hypothesis,
      includeWebSearch,
      models: {
        proponentModel: models.strategy,
        opponentModel: models.answer,
        judgeModel: models.finalAnswer
      }
    }, {
      onSuccess: () => {
        setActiveTab('result')
      }
    })
  }

  return (
    <AppShell>
      <div className="flex flex-col h-full bg-background overflow-hidden font-sans">
        <div className="flex-shrink-0 p-6 pb-2">
          <div className="flex items-center gap-3 mb-6">
            <Scale className="h-8 w-8 text-primary" />
            <h1 className="text-xl md:text-3xl font-bold tracking-tight">
              {t.navigation?.hypothesisMode || "Hypothesis Mode"}
            </h1>
          </div>

          <div className="flex-shrink-0 mb-6">
            <Tabs
              value={activeTab}
              onValueChange={(value) => setActiveTab(value as 'input' | 'result')}
              className="w-full"
            >
              <TabsList className="grid w-full grid-cols-2 p-1 bg-muted/30 backdrop-blur-sm border border-border/50 rounded-xl">
                <TabsTrigger
                  value="input"
                  className={cn(
                    "gap-2 py-2.5 transition-all duration-300 rounded-lg",
                    activeTab === 'input' && "bg-background text-primary shadow-[0_0_15px_rgba(var(--primary-rgb),0.2)] dark:shadow-[0_0_20px_rgba(var(--primary-rgb),0.3)] ring-1 ring-primary/20"
                  )}
                >
                  <FileText className="h-4 w-4" />
                  <span className="font-medium">Setup & Run</span>
                </TabsTrigger>
                <TabsTrigger
                  value="result"
                  disabled={!data && !isPending}
                  className={cn(
                    "gap-2 py-2.5 transition-all duration-300 rounded-lg",
                    activeTab === 'result' && "bg-background text-primary shadow-[0_0_15px_rgba(var(--primary-rgb),0.2)] dark:shadow-[0_0_20px_rgba(var(--primary-rgb),0.3)] ring-1 ring-primary/20"
                  )}
                >
                  {isPending ? <LoadingSpinner size="sm" /> : <BarChart3 className="h-4 w-4" />}
                  <span className="font-medium">Evaluation Result</span>
                </TabsTrigger>
              </TabsList>
            </Tabs>
          </div>
        </div>

        <div className="flex-1 px-6 pb-6 pt-2 overflow-y-auto min-h-0 custom-scrollbar">
          <div className="max-w-6xl mx-auto h-full">
            {activeTab === 'input' && (
              <div className="animate-in fade-in slide-in-from-bottom-2 duration-300 space-y-6">
                <Card className="border-2 border-primary/10 shadow-lg overflow-hidden">
                  <CardHeader className="bg-muted/30 pb-4">
                    <CardTitle className="text-xl flex items-center gap-2">
                      <Scale className="h-5 w-5 text-primary" /> Test a Hypothesis
                    </CardTitle>
                    <CardDescription>
                      Enter a hypothesis or comparison. The engine will debate the point using your knowledge base and web searches.
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="pt-6 space-y-6">
                    <div className="space-y-3">
                      <Label htmlFor="hypothesis-input" className="text-base font-semibold">Your Hypothesis</Label>
                      <Textarea
                        id="hypothesis-input"
                        placeholder="e.g. Will React outperform Vue in large scale applications?"
                        value={hypothesis}
                        onChange={(e) => setHypothesis(e.target.value)}
                        className="resize-none text-base min-h-[150px] border-primary/20 focus-visible:ring-primary rounded-xl"
                        onKeyDown={(e) => {
                          if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
                            e.preventDefault()
                            handleRunHypothesis()
                          }
                        }}
                      />
                      <div className="flex justify-between items-center text-xs text-muted-foreground bg-muted/20 p-2 rounded-lg border border-border/50">
                        <span className="flex items-center gap-1.5"><AlertCircle className="h-3 w-3" /> Format: "Will X outperform Y?"</span>
                        <span>Press <kbd className="px-1.5 py-0.5 rounded border bg-background font-sans text-[10px]">Cmd/Ctrl+Enter</kbd> to run</span>
                      </div>
                    </div>

                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-2xl border bg-card/50 backdrop-blur-sm shadow-sm">
                      <div className="flex items-center gap-4">
                        <div className="flex items-center space-x-3">
                          <Switch
                            id="web-search"
                            checked={includeWebSearch}
                            onCheckedChange={setIncludeWebSearch}
                          />
                          <Label htmlFor="web-search" className="flex items-center gap-2 cursor-pointer font-medium">
                            <Globe className="h-4 w-4 text-primary" /> {t.common?.includeWebSearch || "Include Web Search"}
                          </Label>
                        </div>
                      </div>

                      <div className="flex items-center gap-3">
                        <div className="flex gap-2 text-[10px] flex-wrap items-center">
                          <span className="text-muted-foreground font-medium uppercase tracking-wider mr-1">Agents:</span>
                          <Badge variant="outline" className="opacity-90 bg-primary/5 border-primary/20 px-2 py-0">
                            Prop: {resolveModelName(customModels?.strategy || modelDefaults?.default_chat_model)}
                          </Badge>
                          <Badge variant="outline" className="opacity-90 bg-primary/5 border-primary/20 px-2 py-0">
                            Opp: {resolveModelName(customModels?.answer || modelDefaults?.default_chat_model)}
                          </Badge>
                          <Badge variant="outline" className="opacity-90 bg-primary/5 border-primary/20 px-2 py-0">
                            Judge: {resolveModelName(customModels?.finalAnswer || modelDefaults?.default_chat_model)}
                          </Badge>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setShowAdvancedModels(true)}
                          className="h-8 py-1 px-3 border border-border/50 hover:bg-muted rounded-lg"
                        >
                          <Settings className="h-3.5 w-3.5 mr-2" />
                          Configure
                        </Button>
                      </div>
                    </div>

                    <Button 
                      size="lg" 
                      className="w-full text-base h-14 rounded-2xl shadow-lg shadow-primary/20 transition-all hover:shadow-primary/30 active:scale-[0.98]" 
                      onClick={handleRunHypothesis}
                      disabled={isPending || !hypothesis.trim()}
                    >
                      {isPending ? (
                        <>
                          <LoadingSpinner size="sm" className="mr-3" />
                          Orchestrating Debate...
                        </>
                      ) : (
                        <>
                          <Play className="h-5 w-5 mr-3 fill-current" />
                          Run Hypothesis Engine
                        </>
                      )}
                    </Button>
                    
                    {isError && (
                      <div className="p-4 bg-destructive/10 text-destructive rounded-xl border border-destructive/20 flex items-start gap-4 mt-4 animate-in shake duration-500">
                        <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" />
                        <div>
                          <h4 className="font-bold">Error running hypothesis</h4>
                          <p className="text-sm opacity-90 leading-snug">{error?.message || "An unknown error occurred"}</p>
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>
            )}

            {activeTab === 'result' && (
              <div className="h-full animate-in fade-in slide-in-from-bottom-2 duration-300 pb-12">
                {isPending ? (
                  <div className="flex flex-col items-center justify-center py-32 space-y-6">
                    <div className="relative">
                      <LoadingSpinner size="lg" className="h-16 w-16" />
                      <Scale className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-6 w-6 text-primary animate-pulse" />
                    </div>
                    <div className="text-center space-y-2">
                      <p className="text-xl font-bold tracking-tight">Debate in Progress</p>
                      <p className="text-muted-foreground text-sm max-w-xs mx-auto">Gathering internal evidence and debating viewpoints across multiple models...</p>
                    </div>
                  </div>
                ) : data ? (
                  <HypothesisReport data={data} />
                ) : (
                  <div className="flex flex-col items-center justify-center py-32 text-muted-foreground">
                    <BarChart3 className="h-16 w-16 opacity-10 mb-6" />
                    <p className="font-medium">Run a hypothesis to see results here.</p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        <AdvancedModelsDialog
          open={showAdvancedModels}
          onOpenChange={setShowAdvancedModels}
          defaultModels={{
            strategy: customModels?.strategy || modelDefaults?.default_chat_model || '',
            answer: customModels?.answer || modelDefaults?.default_chat_model || '',
            finalAnswer: customModels?.finalAnswer || modelDefaults?.default_chat_model || ''
          }}
          onSave={setCustomModels}
        />
      </div>
    </AppShell>
  )
}
