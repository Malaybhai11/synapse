import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import { HypothesisResponse, EvidenceItem } from '@/lib/types/hypothesis'
import { Scale, CheckCircle2, XCircle, Globe, Book, ExternalLink } from 'lucide-react'

interface HypothesisReportProps {
  data: HypothesisResponse
}

export function HypothesisReport({ data }: HypothesisReportProps) {
  const renderEvidence = (items: EvidenceItem[], side: 'for' | 'against') => {
    if (!items || items.length === 0) {
      return (
        <div className="flex flex-col items-center justify-center py-8 text-muted-foreground bg-muted/20 rounded-lg border border-dashed">
          <p className="text-sm">No significant evidence found.</p>
        </div>
      )
    }

    return (
      <div className="space-y-4">
        {items.map((item) => (
          <Card key={item.id} className={`border-l-4 ${side === 'for' ? 'border-l-emerald-500' : 'border-l-rose-500'} shadow-sm hover:shadow transition-shadow`}>
            <CardContent className="p-4 space-y-2">
              <div className="flex items-start justify-between gap-2">
                <p className="text-sm leading-relaxed">{item.snippet}</p>
              </div>
              <div className="flex items-center gap-2 mt-2 pt-2 border-t border-border/50">
                <Badge variant="outline" className="text-[10px] leading-tight px-1.5 font-medium flex items-center gap-1 opacity-80">
                  {item.sourceType === 'web' ? <Globe className="h-3 w-3" /> : <Book className="h-3 w-3" />}
                  {item.sourceType === 'web' ? 'Web' : 'Notebook'}
                </Badge>
                {item.url ? (
                  <a href={item.url} target="_blank" rel="noopener noreferrer" className="text-xs text-primary hover:underline flex items-center gap-1 truncate max-w-[200px]">
                    {item.title} <ExternalLink className="h-3 w-3" />
                  </a>
                ) : (
                  <span className="text-xs text-muted-foreground truncate max-w-[200px]">{item.title}</span>
                )}
                {item.score > 0 && (
                  <span className="text-[10px] text-muted-foreground ml-auto" title="Relevance Score">
                    Score: {item.score.toFixed(2)}
                  </span>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  // Determine color based on confidence score (assuming 0-100)
  const confidenceColor = 
    data.confidenceScore >= 75 ? "bg-emerald-500" : 
    data.confidenceScore >= 40 ? "bg-amber-500" : 
    "bg-rose-500"

  return (
    <div className="space-y-6">
      {/* Formal Hypothesis & Confidence */}
      <Card className="border-t-4 border-t-primary shadow-md">
        <CardContent className="pt-6">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
            <div className="space-y-2 flex-1">
              <h2 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
                <Scale className="h-4 w-4" /> Evaluated Hypothesis
              </h2>
              <p className="text-xl md:text-2xl font-bold leading-tight">{data.hypothesis}</p>
            </div>
            
            <div className="flex flex-col items-center bg-muted/30 p-4 rounded-full aspect-square justify-center min-w-[120px] shadow-inner">
              <span className="text-3xl font-black">{data.confidenceScore}%</span>
              <span className="text-xs font-medium uppercase tracking-widest text-muted-foreground mt-1">Confidence</span>
            </div>
          </div>
          
          <div className="mt-6 pt-6 border-t">
            <h3 className="text-sm font-semibold text-muted-foreground mb-3">Confidence Meter</h3>
            <div className="space-y-1">
              <div className="flex justify-between text-xs font-medium">
                <span className="text-rose-500">Unlikely</span>
                <span className="text-amber-500">Inconclusive</span>
                <span className="text-emerald-500">Highly Likely</span>
              </div>
              <Progress value={data.confidenceScore} className="h-3 bg-muted" indicatorClassName={confidenceColor} />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* The Debate Board */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Proponent (Evidence For) */}
        <div className="space-y-4">
          <div className="flex items-center gap-2 pb-2 border-b-2 border-emerald-500/30">
            <CheckCircle2 className="h-5 w-5 text-emerald-500" />
            <h3 className="text-lg font-semibold text-emerald-600 dark:text-emerald-400">Supporting Evidence</h3>
            <Badge variant="secondary" className="ml-auto bg-emerald-500/10 text-emerald-600 hover:bg-emerald-500/20">{data.proponentEvidence.length}</Badge>
          </div>
          {renderEvidence(data.proponentEvidence, 'for')}
        </div>

        {/* Opponent (Evidence Against) */}
        <div className="space-y-4">
          <div className="flex items-center gap-2 pb-2 border-b-2 border-rose-500/30">
            <XCircle className="h-5 w-5 text-rose-500" />
            <h3 className="text-lg font-semibold text-rose-600 dark:text-rose-400">Opposing Evidence</h3>
            <Badge variant="secondary" className="ml-auto bg-rose-500/10 text-rose-600 hover:bg-rose-500/20">{data.opponentEvidence.length}</Badge>
          </div>
          {renderEvidence(data.opponentEvidence, 'against')}
        </div>
      </div>

      {/* The Judge Synthesis */}
      <Card className="bg-primary/5 border-primary/20 shadow-sm relative overflow-hidden">
        <div className="absolute top-0 left-0 w-1 h-full bg-primary" />
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Scale className="h-5 w-5 text-primary" /> The Judge's Synthesis
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="prose prose-sm dark:prose-invert max-w-none text-base leading-relaxed">
            {data.judgeSynthesis || "No synthesis available."}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
