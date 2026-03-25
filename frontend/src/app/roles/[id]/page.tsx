"use client";

import { useParams } from "next/navigation";
import { usePolling } from "@/hooks/use-polling";
import { Header } from "@/components/layout/Header";
import { UploadZone } from "@/components/resumes/UploadZone";
import { ScoreCard } from "@/components/scores/ScoreCard";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { JDQualityNotice } from "@/components/roles/JDQualityNotice";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { useState } from "react";
import { Loader2, BarChart3, Eye, EyeOff } from "lucide-react";

export default function RoleDetailPage() {
  const params = useParams();
  const roleId = params.id as string;
  const {
    data: role,
    mutate: mutateRole,
    error: roleError,
    isLoading: roleLoading,
  } = usePolling<any>(`/api/roles/${roleId}`, 5000);
  const {
    data: resumes,
    mutate: mutateResumes,
    error: resumesError,
    isLoading: resumesLoading,
  } = usePolling<any[]>(`/api/roles/${roleId}/resumes`, 3000);
  const [analyzingJD, setAnalyzingJD] = useState(false);

  const scoredResumes = resumes?.filter((r: any) => r.status === "scored") || [];
  const processingResumes =
    resumes?.filter((r: any) => ["pending", "processing", "parsing", "extracting", "scoring"].includes(r.status)) || [];
  const duplicateResumes = resumes?.filter((r: any) => r.status === "duplicate") || [];
  const errorResumes = resumes?.filter((r: any) => r.status === "error") || [];

  const handleAnalyzeJD = async () => {
    setAnalyzingJD(true);
    try {
      await api.analyzeJD(roleId);
      mutateRole();
      toast.success("JD analysis complete");
    } catch (e: any) {
      toast.error(e.message);
    } finally {
      setAnalyzingJD(false);
    }
  };

  if (roleError) {
    return (
      <div className="p-6 max-w-3xl mx-auto">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-sm font-medium text-red-800">Failed to load role.</p>
          <p className="text-xs text-red-600 mt-1">{roleError.message}</p>
          <div className="mt-3 flex gap-2">
            <Button onClick={() => mutateRole()} disabled={roleLoading}>
              {roleLoading ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : null}
              Retry
            </Button>
          </div>
        </div>
      </div>
    );
  }

  if (!role) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div>
      <Header
        title={role.title}
        subtitle={`${resumes?.length || 0} candidates · ${scoredResumes.length} scored${role.blind_mode ? " · Blind Mode" : ""}`}
      />
      <div className="p-6 space-y-6">
        {resumesError && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-sm font-medium text-red-800">Failed to load resumes.</p>
            <p className="text-xs text-red-600 mt-1">{resumesError.message}</p>
            <div className="mt-3">
              <Button onClick={() => mutateResumes()} disabled={resumesLoading}>
                {resumesLoading ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : null}
                Retry
              </Button>
            </div>
          </div>
        )}
        {/* JD Quality Section */}
        <div className="flex items-center gap-3">
          {!role.jd_quality_report && (
            <Button variant="outline" size="sm" onClick={handleAnalyzeJD} disabled={analyzingJD}>
              {analyzingJD ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <BarChart3 className="h-4 w-4 mr-2" />}
              Analyze JD Quality
            </Button>
          )}
          <Badge variant="outline" className="gap-1">
            {role.blind_mode ? <EyeOff className="h-3 w-3" /> : <Eye className="h-3 w-3" />}
            {role.blind_mode ? "Blind Mode On" : "Blind Mode Off"}
          </Badge>
        </div>

        {role.jd_quality_report && <JDQualityNotice report={role.jd_quality_report} />}

        {/* Upload Zone */}
        <UploadZone roleId={roleId} onUploadComplete={() => mutateResumes()} />

        {/* Processing Resumes */}
        {processingResumes.length > 0 && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm font-medium text-blue-800 flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin" />
              Processing {processingResumes.length} resume{processingResumes.length > 1 ? "s" : ""}...
            </p>
            <div className="mt-2 space-y-1">
              {processingResumes.map((r: any) => (
                <p key={r.id} className="text-xs text-blue-600">
                  {r.original_filename} — {r.status}
                </p>
              ))}
            </div>
          </div>
        )}

        {/* Duplicate Resumes */}
        {duplicateResumes.length > 0 && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <p className="text-sm font-medium text-yellow-900">
              {duplicateResumes.length} duplicate{duplicateResumes.length > 1 ? "s" : ""} detected
            </p>
            <div className="mt-2 space-y-1">
              {duplicateResumes.map((r: any) => (
                <p key={r.id} className="text-xs text-yellow-800">
                  {r.original_filename}
                </p>
              ))}
            </div>
          </div>
        )}

        {/* Error Resumes */}
        {errorResumes.length > 0 && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-sm font-medium text-red-800">
              {errorResumes.length} resume{errorResumes.length > 1 ? "s" : ""} failed to process
            </p>
            <div className="mt-2 space-y-1">
              {errorResumes.map((r: any) => (
                <p key={r.id} className="text-xs text-red-600">
                  {r.original_filename}: {r.error_message || "Unknown error"}
                </p>
              ))}
            </div>
          </div>
        )}

        {/* Ranked Candidates */}
        {scoredResumes.length > 0 && (
          <div>
            <h2 className="text-lg font-semibold mb-3">
              Ranked Candidates ({scoredResumes.length})
            </h2>
            <div className="space-y-3">
              {scoredResumes
                .sort((a: any, b: any) => {
                  const scoreA = a.score?.overall_score ?? 0;
                  const scoreB = b.score?.overall_score ?? 0;
                  return scoreB - scoreA;
                })
                .map((resume: any, index: number) => (
                  <ScoreCard
                    key={resume.id}
                    resume={resume}
                    rank={index + 1}
                    roleId={roleId}
                    blindMode={role.blind_mode}
                    onDelete={() => mutateResumes()}
                  />
                ))}
            </div>
          </div>
        )}

        {resumes && resumes.length === 0 && (
          <div className="text-center py-12 text-muted-foreground">
            <p>No resumes uploaded yet. Drag and drop files above to get started.</p>
          </div>
        )}
      </div>
    </div>
  );
}
