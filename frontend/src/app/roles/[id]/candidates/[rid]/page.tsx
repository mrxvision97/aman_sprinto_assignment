"use client";

import { useParams, useRouter } from "next/navigation";
import useSWR from "swr";
import { fetcher, api } from "@/lib/api";
import { Header } from "@/components/layout/Header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { useState } from "react";
import { toast } from "sonner";
import {
  ChevronLeft, Copy, CheckCircle, AlertTriangle, Lightbulb,
  Eye, EyeOff, ChevronDown, ChevronUp, Trash2
} from "lucide-react";
import Link from "next/link";

const recommendationColors: Record<string, string> = {
  strongly_recommend: "bg-green-100 text-green-800 border-green-200",
  recommend: "bg-emerald-100 text-emerald-800 border-emerald-200",
  maybe: "bg-amber-100 text-amber-800 border-amber-200",
  do_not_advance: "bg-red-100 text-red-800 border-red-200",
};

const recommendationLabels: Record<string, string> = {
  strongly_recommend: "Strongly Recommend",
  recommend: "Recommend",
  maybe: "Screen First",
  do_not_advance: "Do Not Advance",
};

function DimensionBar({ dim, index }: { dim: any; index: number }) {
  const [expanded, setExpanded] = useState(false);
  const score = dim.score ?? 0;
  const pct = (score / 10) * 100;
  const color = score >= 7 ? "bg-green-500" : score >= 5 ? "bg-amber-500" : "bg-red-500";

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-3">
        <p className="w-36 text-sm font-medium shrink-0">{dim.dimension}</p>
        <div className="flex-1 h-2.5 bg-muted rounded-full overflow-hidden">
          <div className={`h-full rounded-full transition-all ${color}`} style={{ width: `${pct}%` }} />
        </div>
        <span className="w-8 text-sm font-bold text-right">{score.toFixed(1)}</span>
        <button type="button" onClick={() => setExpanded(!expanded)} className="text-muted-foreground hover:text-foreground">
          {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </button>
      </div>
      {expanded && (
        <div className="ml-36 pl-3 border-l space-y-1">
          {dim.evidence?.map((e: string, i: number) => (
            <p key={i} className="text-xs text-muted-foreground italic">"{e}"</p>
          ))}
          {dim.gaps?.length > 0 && (
            <p className="text-xs text-amber-600">Gap: {dim.gaps.join("; ")}</p>
          )}
        </div>
      )}
    </div>
  );
}

export default function CandidateDetailPage() {
  const params = useParams();
  const router = useRouter();
  const roleId = params.id as string;
  const resumeId = params.rid as string;

  const { data: resume, mutate: mutateResume, error: resumeError } = useSWR<any>(
    `/api/resumes/${resumeId}`,
    fetcher,
    { refreshInterval: 3000 }
  );
  const { data: role, error: roleError, mutate: mutateRole } = useSWR<any>(`/api/roles/${roleId}`, fetcher);

  const [showReasoning, setShowReasoning] = useState(false);
  const [copied, setCopied] = useState(false);
  const [deleting, setDeleting] = useState(false);

  if (resumeError) {
    return (
      <div className="p-6 max-w-3xl mx-auto">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-sm font-medium text-red-800">Failed to load resume.</p>
          <p className="text-xs text-red-600 mt-1">{resumeError.message}</p>
          <div className="mt-3">
            <Button onClick={() => mutateResume()} type="button">
              Retry
            </Button>
          </div>
        </div>
      </div>
    );
  }

  if (!resume) {
    return <div className="flex items-center justify-center py-20">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
    </div>;
  }

  const score = resume.score;
  const blindMode = role?.blind_mode ?? true;
  const candidateName = blindMode
    ? null
    : resume.extracted_fields?.full_name?.value || resume.original_filename;

  const handleCopy = async () => {
    const summary = score?.recruiter_summary;
    if (summary == null) return;
    try {
      if (!navigator.clipboard?.writeText) {
        throw new Error("Clipboard not available in this browser");
      }
      await navigator.clipboard.writeText(summary);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch (e: any) {
      toast.error(e?.message || "Failed to copy to clipboard");
      setCopied(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm("Delete this resume and its score?")) return;
    setDeleting(true);
    try {
      await api.deleteResume(resumeId);
      toast.success("Resume deleted");
      router.push(`/roles/${roleId}`);
    } catch (e: any) {
      toast.error(e.message);
      setDeleting(false);
    }
  };

  return (
    <div>
      <Header
        title={candidateName || (blindMode ? "Candidate (Blind Mode)" : resume.original_filename)}
        subtitle={resume.original_filename}
      />
      <div className="p-6 max-w-4xl space-y-6">
        {roleError && (
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
            <p className="text-sm font-medium text-amber-800">Failed to load role settings.</p>
            <p className="text-xs text-amber-700 mt-1">{roleError.message}</p>
            <div className="mt-3">
              <Button onClick={() => mutateRole()} type="button" variant="outline">
                Retry
              </Button>
            </div>
          </div>
        )}
        {/* Back + Actions */}
        <div className="flex items-center justify-between">
          <Link href={`/roles/${roleId}`} className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
            <ChevronLeft className="h-4 w-4" /> Back to candidates
          </Link>
          <div className="flex items-center gap-2">
            {resume.ai_authorship_signal && resume.ai_authorship_signal !== "none" && (
              <Badge variant="outline" className="text-xs">
                AI-written signal: {resume.ai_authorship_signal}
              </Badge>
            )}
            <Button variant="outline" size="sm" onClick={handleDelete} disabled={deleting} type="button">
              <Trash2 className="h-4 w-4 mr-1" />
              Delete
            </Button>
          </div>
        </div>

        {/* Overall Score Header */}
        {score && (
          <Card>
            <CardContent className="py-5">
              <div className="flex items-center gap-6 flex-wrap">
                <div className="text-center">
                  <div className="text-4xl font-bold">{Number(score.overall_score).toFixed(1)}</div>
                  <div className="text-xs text-muted-foreground">/ 10</div>
                </div>
                <div className="flex-1">
                  <div className="w-full h-3 bg-muted rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full bg-primary"
                      style={{ width: `${(Number(score.overall_score) / 10) * 100}%` }}
                    />
                  </div>
                </div>
                {score.recommendation && (
                  <Badge className={`px-4 py-1.5 text-sm ${recommendationColors[score.recommendation]}`} variant="outline">
                    {recommendationLabels[score.recommendation] || score.recommendation}
                  </Badge>
                )}
                {score.confidence && (
                  <Badge variant="outline">
                    {score.confidence === "high" ? "✓" : score.confidence === "medium" ? "~" : "↓"} {score.confidence} confidence
                  </Badge>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Dimensional Scores */}
        {score?.dimensional_scores?.length > 0 && (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Dimension Scores</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {score.dimensional_scores.map((dim: any, i: number) => (
                <DimensionBar key={i} dim={dim} index={i} />
              ))}
            </CardContent>
          </Card>
        )}

        {/* Strengths & Concerns */}
        {(score?.strengths?.length > 0 || score?.concerns?.length > 0) && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {score?.strengths?.length > 0 && (
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-base flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    Strengths
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {score.strengths.map((s: any, i: number) => (
                    <div key={i} className="space-y-1">
                      <p className="text-sm font-medium">{s.point}</p>
                      <p className="text-xs text-muted-foreground italic">"{s.evidence}"</p>
                    </div>
                  ))}
                </CardContent>
              </Card>
            )}

            {score?.concerns?.length > 0 && (
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-base flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4 text-amber-500" />
                    Concerns
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {score.concerns.map((c: any, i: number) => (
                    <div key={i} className="space-y-1">
                      <p className="text-sm font-medium">{c.point}</p>
                      <p className="text-xs text-muted-foreground italic">"{c.evidence}"</p>
                      {c.suggested_question && (
                        <p className="text-xs text-blue-600">→ Ask: {c.suggested_question}</p>
                      )}
                    </div>
                  ))}
                </CardContent>
              </Card>
            )}
          </div>
        )}

        {/* Recruiter Summary */}
        {score?.recruiter_summary && (
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">Recruiter Summary</CardTitle>
                <Button variant="ghost" size="sm" onClick={handleCopy} type="button">
                  {copied ? <CheckCircle className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
                  <span className="ml-1 text-xs">{copied ? "Copied!" : "Copy"}</span>
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm leading-relaxed">{score.recruiter_summary}</p>
            </CardContent>
          </Card>
        )}

        {/* Suggested Interview Questions */}
        {score?.suggested_questions?.length > 0 && (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <Lightbulb className="h-4 w-4 text-amber-500" />
                Suggested Interview Questions
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ol className="space-y-3">
                {score.suggested_questions.map((q: any, i: number) => (
                  <li key={i} className="space-y-1">
                    <p className="text-sm font-medium">{i + 1}. {q.question}</p>
                    {q.addresses && (
                      <p className="text-xs text-muted-foreground ml-4">Addresses: {q.addresses}</p>
                    )}
                  </li>
                ))}
              </ol>
            </CardContent>
          </Card>
        )}

        {/* Contradiction Flags */}
        {resume.contradiction_flags?.length > 0 && (
          <Card className="border-amber-200">
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2 text-amber-700">
                <AlertTriangle className="h-4 w-4" />
                Contradiction Flags
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {resume.contradiction_flags.map((f: any, i: number) => (
                <div key={i} className="flex items-start gap-2 text-sm">
                  <AlertTriangle className="h-4 w-4 text-amber-500 mt-0.5 shrink-0" />
                  <span>{f.description || f.type}</span>
                </div>
              ))}
            </CardContent>
          </Card>
        )}

        {/* Extracted Fields */}
        {resume.extracted_fields && (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Extracted Information</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {Object.entries(resume.extracted_fields).map(([key, val]: [string, any]) => {
                  if (val?.value === null || val?.value === undefined) return null;
                  return (
                    <div key={key} className="space-y-1">
                      <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                        {key.replace(/_/g, " ")}
                      </p>
                      <p className="text-sm">{Array.isArray(val.value) ? val.value.join(", ") : String(val.value)}</p>
                      {val.evidence && (
                        <p className="text-xs text-muted-foreground italic">"{val.evidence}"</p>
                      )}
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Show AI Reasoning Toggle */}
        {score?.raw_scores && (
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">AI Reasoning</CardTitle>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowReasoning(!showReasoning)}
                  type="button"
                >
                  {showReasoning ? <EyeOff className="h-4 w-4 mr-1" /> : <Eye className="h-4 w-4 mr-1" />}
                  {showReasoning ? "Hide" : "Show"} reasoning
                </Button>
              </div>
            </CardHeader>
            {showReasoning && (
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <p className="text-xs font-semibold text-muted-foreground mb-2">STAGE 1 — Initial Scores</p>
                    <pre className="text-xs bg-muted p-3 rounded overflow-x-auto whitespace-pre-wrap">
                      {JSON.stringify(score.raw_scores, null, 2)}
                    </pre>
                  </div>
                  {score.critique && (
                    <div>
                      <p className="text-xs font-semibold text-muted-foreground mb-2">STAGE 2 — Adversarial Critique</p>
                      <pre className="text-xs bg-muted p-3 rounded overflow-x-auto whitespace-pre-wrap">
                        {JSON.stringify(score.critique, null, 2)}
                      </pre>
                    </div>
                  )}
                  <div>
                    <p className="text-xs font-semibold text-muted-foreground mb-2">STAGE 3 — Final Output (Blended + Synthesis)</p>
                    <pre className="text-xs bg-muted p-3 rounded overflow-x-auto whitespace-pre-wrap">
                      {JSON.stringify(
                        {
                          dimensional_scores: score.dimensional_scores,
                          overall_score: score.overall_score,
                          recommendation: score.recommendation,
                          confidence: score.confidence,
                          strengths: score.strengths,
                          concerns: score.concerns,
                          suggested_questions: score.suggested_questions,
                          recruiter_summary: score.recruiter_summary,
                        },
                        null,
                        2
                      )}
                    </pre>
                  </div>
                </div>
              </CardContent>
            )}
          </Card>
        )}
      </div>
    </div>
  );
}
