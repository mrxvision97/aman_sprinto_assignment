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
import { Loader2, BarChart3, Eye, EyeOff, Search, X } from "lucide-react";
import { Input } from "@/components/ui/input";

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
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<any[] | null>(null);
  const [searching, setSearching] = useState(false);

  const scoredResumes = resumes?.filter((r: any) => r.status === "scored") || [];
  const processingResumes =
    resumes?.filter((r: any) => ["pending", "processing", "parsing", "extracting", "scoring"].includes(r.status)) || [];
  const duplicateResumes = resumes?.filter((r: any) => r.status === "duplicate") || [];
  const errorResumes = resumes?.filter((r: any) => r.status === "error") || [];

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    setSearching(true);
    try {
      const results = await api.searchResumes(roleId, searchQuery.trim());
      setSearchResults(results);
    } catch (e: any) {
      toast.error(e.message);
    } finally {
      setSearching(false);
    }
  };

  const clearSearch = () => {
    setSearchQuery("");
    setSearchResults(null);
  };

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

        {/* Semantic Search */}
        {scoredResumes.length > 0 && (
          <form onSubmit={handleSearch} className="flex items-center gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder='Search candidates… e.g. "Python + NLP experience"'
                className="pl-9 pr-4"
              />
            </div>
            <button
              type="submit"
              disabled={searching || !searchQuery.trim()}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-md bg-primary text-primary-foreground text-sm font-medium disabled:opacity-50 hover:bg-primary/90 transition-colors"
            >
              {searching ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
              Search
            </button>
            {searchResults !== null && (
              <button type="button" onClick={clearSearch} className="p-2 rounded-md hover:bg-muted text-muted-foreground hover:text-foreground transition-colors">
                <X className="h-4 w-4" />
              </button>
            )}
          </form>
        )}

        {/* Search Results */}
        {searchResults !== null && (
          <div>
            <h2 className="text-lg font-semibold mb-3">
              Search Results ({searchResults.length})
              <span className="text-sm font-normal text-muted-foreground ml-2">for "{searchQuery}"</span>
            </h2>
            {searchResults.length === 0 ? (
              <p className="text-sm text-muted-foreground py-4">No matching candidates found.</p>
            ) : (
              <div className="space-y-3">
                {searchResults.map((resume: any, index: number) => (
                  <div key={resume.id} className="relative">
                    <ScoreCard
                      resume={resume}
                      rank={index + 1}
                      roleId={roleId}
                      blindMode={role.blind_mode}
                      onDelete={() => { clearSearch(); mutateResumes(); }}
                    />
                    <span className="absolute top-3 right-12 text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded-full">
                      {Math.round(resume.similarity * 100)}% match
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Ranked Candidates */}
        {searchResults === null && scoredResumes.length > 0 && (
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
