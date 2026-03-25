"use client";

import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { StatusBadge } from "@/components/resumes/StatusBadge";
import { Trash2 } from "lucide-react";
import { api } from "@/lib/api";
import { toast } from "sonner";

const recommendationColors: Record<string, string> = {
  strongly_recommend: "bg-green-100 text-green-800",
  recommend: "bg-emerald-100 text-emerald-800",
  maybe: "bg-amber-100 text-amber-800",
  do_not_advance: "bg-red-100 text-red-800",
};

const recommendationLabels: Record<string, string> = {
  strongly_recommend: "Strongly Recommend",
  recommend: "Recommend",
  maybe: "Maybe",
  do_not_advance: "Do Not Advance",
};

function ScoreBar({ score }: { score: number }) {
  const percentage = (score / 10) * 100;
  const color = score >= 7 ? "bg-green-500" : score >= 5 ? "bg-amber-500" : "bg-red-500";

  return (
    <div className="flex items-center gap-2">
      <div className="w-24 h-2 bg-muted rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${percentage}%` }} />
      </div>
      <span className="text-sm font-semibold w-8">{score.toFixed(1)}</span>
    </div>
  );
}

interface ScoreCardProps {
  resume: any;
  rank: number;
  roleId: string;
  blindMode: boolean;
  onDelete?: () => void;
}

export function ScoreCard({ resume, rank, roleId, blindMode, onDelete }: ScoreCardProps) {
  const handleDelete = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!confirm("Delete this candidate?")) return;
    try {
      await api.deleteResume(resume.id);
      toast.success("Candidate deleted");
      onDelete?.();
    } catch {
      toast.error("Failed to delete");
    }
  };
  const score = resume.score;
  const candidateName = blindMode
    ? `Candidate #${rank}`
    : resume.extracted_fields?.full_name?.value || resume.original_filename;

  return (
    <Link href={`/roles/${roleId}/candidates/${resume.id}`}>
      <Card className="hover:shadow-md transition-shadow cursor-pointer">
        <CardContent className="py-4">
          <div className="flex items-center gap-4">
            <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-sm font-bold text-primary shrink-0">
              #{rank}
            </div>

            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <p className="font-medium truncate">{candidateName}</p>
                <StatusBadge status={resume.status} />
                {resume.ai_authorship_signal && resume.ai_authorship_signal !== "none" && (
                  <Badge variant="outline" className="text-xs">
                    AI-written: {resume.ai_authorship_signal}
                  </Badge>
                )}
              </div>
              {score?.recruiter_summary && (
                <p className="text-xs text-muted-foreground mt-1 line-clamp-1">
                  {score.recruiter_summary}
                </p>
              )}
            </div>

            <div className="flex items-center gap-4 shrink-0">
              {score?.overall_score != null && <ScoreBar score={Number(score.overall_score)} />}
              {score?.recommendation && (
                <Badge className={`text-xs ${recommendationColors[score.recommendation] || ""}`} variant="secondary">
                  {recommendationLabels[score.recommendation] || score.recommendation}
                </Badge>
              )}
              {score?.confidence && (
                <Badge variant="outline" className="text-xs">
                  {score.confidence}
                </Badge>
              )}
              <button
                onClick={handleDelete}
                type="button"
                aria-label={`Delete candidate ${candidateName}`}
                className="p-1 rounded hover:bg-red-50 text-muted-foreground hover:text-red-500 transition-colors"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
