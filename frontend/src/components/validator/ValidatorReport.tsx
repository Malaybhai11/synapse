'use client'

import React, { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'
import { ValidatorResponse, Vulnerability, Assumption, Mitigation } from '@/lib/types/validator'
import {
  ShieldAlert,
  Lightbulb,
  Target,
  Brain,
  ChevronDown,
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  Zap
} from 'lucide-react'

const severityConfig = {
  High:   { className: 'border-l-rose-500',    badgeClass: 'bg-rose-500/10 text-rose-600 border-rose-500/20',    icon: <AlertTriangle className="h-3.5 w-3.5" /> },
  Medium: { className: 'border-l-amber-500',   badgeClass: 'bg-amber-500/10 text-amber-600 border-amber-500/20',   icon: <TrendingUp className="h-3.5 w-3.5" /> },
  Low:    { className: 'border-l-emerald-500', badgeClass: 'bg-emerald-500/10 text-emerald-600 border-emerald-500/20', icon: <CheckCircle2 className="h-3.5 w-3.5" /> },
}

const effortConfig = {
  High:   { badgeClass: 'bg-rose-500/10 text-rose-500 border-rose-500/20' },
  Medium: { badgeClass: 'bg-amber-500/10 text-amber-500 border-amber-500/20' },
  Low:    { badgeClass: 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20' },
}

interface ValidatorReportProps {
  data: ValidatorResponse
}

export function ValidatorReport({ data }: ValidatorReportProps) {
  const ReasoningBlock = ({ think, label }: { think?: string; label: string }) => {
    if (!think) return null
    return (
      <Collapsible className="w-full mt-3 bg-muted/20 border border-muted-foreground/10 rounded-lg p-3 group">
        <CollapsibleTrigger className="flex items-center justify-between w-full text-xs font-semibold uppercase tracking-wider text-muted-foreground hover:text-foreground transition-colors">
          <span className="flex items-center gap-2"><Brain className="h-3.5 w-3.5" /> {label} Thought Process</span>
          <ChevronDown className="h-3.5 w-3.5 opacity-50 transition-transform group-data-[state=open]:rotate-180" />
        </CollapsibleTrigger>
        <CollapsibleContent className="mt-3 pt-3 border-t border-muted-foreground/10 text-[13px] text-muted-foreground/80 whitespace-pre-wrap font-mono leading-relaxed">
          {think}
        </CollapsibleContent>
      </Collapsible>
    )
  }

  const riskColor = data.overallRiskScore >= 70 ? 'bg-rose-500' : data.overallRiskScore >= 40 ? 'bg-amber-500' : 'bg-emerald-500'
  const riskLabel = data.overallRiskScore >= 70 ? 'High Risk' : data.overallRiskScore >= 40 ? 'Moderate Risk' : 'Low Risk'
  const riskBadgeClass = data.overallRiskScore >= 70
    ? 'bg-rose-500/10 text-rose-600 border-rose-500/20'
    : data.overallRiskScore >= 40
    ? 'bg-amber-500/10 text-amber-600 border-amber-500/20'
    : 'bg-emerald-500/10 text-emerald-600 border-emerald-500/20'

  const highCount = data.vulnerabilities.filter(v => v.severity === 'High').length
  const medCount  = data.vulnerabilities.filter(v => v.severity === 'Medium').length
  const lowCount  = data.vulnerabilities.filter(v => v.severity === 'Low').length

  return (
    <div className="space-y-6">
      {/* Header Risk Card */}
      <Card className="border-t-4 border-t-primary shadow-md">
        <CardContent className="pt-6">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
            <div className="space-y-2 flex-1">
              <h2 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
                <ShieldAlert className="h-4 w-4" /> Critique Report
              </h2>
              <p className="text-xl md:text-2xl font-bold leading-tight">{data.idea}</p>
            </div>

            <div className="flex flex-col items-center bg-muted/30 p-4 rounded-full aspect-square justify-center min-w-[120px] shadow-inner">
              <span className="text-3xl font-black">{data.overallRiskScore}%</span>
              <span className="text-xs font-medium uppercase tracking-widest text-muted-foreground mt-1">Risk Score</span>
            </div>
          </div>

          <div className="mt-6 pt-6 border-t">
            <div className="flex items-center gap-3 mb-3">
              <h3 className="text-sm font-semibold text-muted-foreground">Overall Risk Level</h3>
              <Badge variant="outline" className={riskBadgeClass}>{riskLabel}</Badge>
            </div>
            <Progress value={data.overallRiskScore} className="h-3 bg-muted" indicatorClassName={riskColor} />
            <div className="flex gap-4 mt-3 text-xs text-muted-foreground">
              {highCount > 0 && <span className="flex items-center gap-1 text-rose-500"><AlertTriangle className="h-3 w-3" />{highCount} High Severity</span>}
              {medCount > 0  && <span className="flex items-center gap-1 text-amber-500"><TrendingUp className="h-3 w-3" />{medCount} Medium Severity</span>}
              {lowCount > 0  && <span className="flex items-center gap-1 text-emerald-500"><CheckCircle2 className="h-3 w-3" />{lowCount} Low Severity</span>}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Assumptions */}
      {data.assumptions.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <Target className="h-5 w-5 text-primary" />
              Core Assumptions Identified
              <Badge variant="secondary" className="ml-auto">{data.assumptions.length}</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <ReasoningBlock think={data.analyzerThink} label="Analyzer" />
            <div className="grid gap-2 mt-3">
              {data.assumptions.map((a: Assumption, i: number) => (
                <div key={i} className="flex items-start gap-3 p-3 rounded-lg bg-muted/30 border border-border/50">
                  <span className="text-xs font-bold text-primary opacity-70 mt-0.5 min-w-[20px]">#{i+1}</span>
                  <p className="text-sm leading-relaxed">{a.description}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Vulnerabilities */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-base">
            <ShieldAlert className="h-5 w-5 text-rose-500" />
            Red Team Attack Surface
            <Badge variant="secondary" className="ml-auto bg-rose-500/10 text-rose-600">{data.vulnerabilities.length} Issues</Badge>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <ReasoningBlock think={data.redTeamThink} label="Red Team" />
          <div className="space-y-3 mt-3">
            {data.vulnerabilities.map((v: Vulnerability, i: number) => {
              const cfg = severityConfig[v.severity] || severityConfig.Medium
              return (
                <Card key={i} className={`border-l-4 ${cfg.className} shadow-sm`}>
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between gap-3 mb-2">
                      <p className="font-semibold text-sm">{v.title}</p>
                      <Badge variant="outline" className={`text-xs shrink-0 flex items-center gap-1 ${cfg.badgeClass}`}>
                        {cfg.icon} {v.severity}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground leading-relaxed">{v.description}</p>
                    <div className="mt-3 pt-2 border-t border-border/40">
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium">Severity Score</span>
                        <Progress value={v.score} className="h-1.5 flex-1 bg-muted" indicatorClassName={cfg.className.replace('border-l-', 'bg-')} />
                        <span className="text-xs font-mono text-muted-foreground">{v.score}/100</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        </CardContent>
      </Card>

      {/* Mitigations */}
      {data.mitigations.length > 0 && (
        <Card className="bg-primary/5 border-primary/20 shadow-sm relative overflow-hidden">
          <div className="absolute top-0 left-0 w-1 h-full bg-primary" />
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Zap className="h-5 w-5 text-primary" />
              Strategist's Mitigations
              <Badge variant="secondary" className="ml-auto">{data.mitigations.length}</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <ReasoningBlock think={data.strategistThink} label="Strategist" />
            <div className="space-y-2 mt-3">
              {data.mitigations.map((m: Mitigation, i: number) => {
                const cfg = effortConfig[m.effort] || effortConfig.Medium
                return (
                  <div key={i} className="flex items-start gap-3 p-3 rounded-lg bg-background/50 border border-border/50 hover:border-primary/30 transition-colors">
                    <Lightbulb className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                    <p className="text-sm leading-relaxed flex-1">{m.description}</p>
                    <Badge variant="outline" className={`text-[10px] shrink-0 ${cfg.badgeClass}`}>
                      {m.effort} Effort
                    </Badge>
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
