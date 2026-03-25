"use client";

import useSWR from "swr";
import { fetcher, api } from "@/lib/api";
import { Header } from "@/components/layout/Header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Loader2, Star } from "lucide-react";

const recommendationColors: Record<string, string> = {
  strongly_recommend: "text-green-600",
  recommend: "text-emerald-600",
  maybe: "text-amber-600",
  do_not_advance: "text-red-600",
};

export default function ComparePage() {
  const { data: roles, error: rolesError, mutate: mutateRoles } = useSWR<any[]>("/api/roles", fetcher);
  const [selectedRole, setSelectedRole] = useState<string>("");
  const [selectedResume, setSelectedResume] = useState<string>("");
  const [compareRoles, setCompareRoles] = useState<string[]>([]);
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const { data: sourceRole } = useSWR<any>(
    selectedRole ? `/api/roles/${selectedRole}` : null,
    fetcher
  );

  const {
    data: resumes,
    error: resumesError,
    mutate: mutateResumes,
  } = useSWR<any[]>(selectedRole ? `/api/roles/${selectedRole}/resumes` : null, fetcher);
  const scoredResumes = resumes?.filter((r: any) => r.status === "scored") || [];
  const blindMode = sourceRole?.blind_mode ?? true;

  useEffect(() => {
    setResults([]);
  }, [selectedRole, selectedResume]);

  const toggleCompareRole = (roleId: string) => {
    setCompareRoles(prev => prev.includes(roleId) ? prev.filter(r => r !== roleId) : [...prev, roleId]);
  };

  const handleCompare = async () => {
    if (!selectedResume || compareRoles.length < 2) {
      toast.error("Select a resume and at least 2 roles to compare");
      return;
    }
    setLoading(true);
    try {
      const data = await api.multiRoleScore(selectedResume, compareRoles);
      setResults(data);
    } catch (e: any) {
      toast.error(e.message);
    } finally {
      setLoading(false);
    }
  };

  const dimensions = results.length > 0 && results[0].dimensional_scores
    ? results[0].dimensional_scores.map((d: any) => d.dimension)
    : [];

  const bestRole = results.length > 0
    ? results.reduce((best, r) => (Number(r.overall_score) > Number(best.overall_score || 0) ? r : best), results[0])
    : null;

  if (rolesError) {
    return (
      <div className="p-6 max-w-3xl mx-auto">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-sm font-medium text-red-800">Failed to load roles.</p>
          <p className="text-xs text-red-600 mt-1">{rolesError.message}</p>
          <div className="mt-3">
            <Button onClick={() => mutateRoles()} type="button">
              Retry
            </Button>
          </div>
        </div>
      </div>
    );
  }

  if (!roles) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    );
  }

  return (
    <div>
      <Header title="Multi-Role Comparison" subtitle="See how one candidate fits multiple roles simultaneously" />
      <div className="p-6 max-w-5xl space-y-6">

        <Card>
          <CardHeader><CardTitle className="text-base">Setup Comparison</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Select Source Role (to pick candidate from)</Label>
                <select
                  className="w-full border rounded-md px-3 py-2 text-sm"
                  value={selectedRole}
                  onChange={e => { setSelectedRole(e.target.value); setSelectedResume(""); }}
                >
                  <option value="">— Choose role —</option>
                  {roles?.map((r: any) => <option key={r.id} value={r.id}>{r.title}</option>)}
                </select>
              </div>
              <div className="space-y-2">
                <Label>Select Candidate</Label>
                {resumesError && (
                  <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                    <p className="text-sm font-medium text-red-800">Failed to load candidates.</p>
                    <p className="text-xs text-red-600 mt-1">{resumesError.message}</p>
                    <div className="mt-3">
                      <Button onClick={() => mutateResumes()} type="button" variant="outline">
                        Retry
                      </Button>
                    </div>
                  </div>
                )}
                <select
                  className="w-full border rounded-md px-3 py-2 text-sm"
                  value={selectedResume}
                  onChange={e => setSelectedResume(e.target.value)}
                  disabled={!selectedRole}
                >
                  <option value="">— Choose candidate —</option>
                  {scoredResumes.map((r: any, index: number) => (
                    <option key={r.id} value={r.id}>
                      {blindMode ? `Candidate #${index + 1}` : (r.extracted_fields?.full_name?.value || r.original_filename)}
                      {r.score?.overall_score ? ` (${Number(r.score.overall_score).toFixed(1)})` : ""}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="space-y-2">
              <Label>Select Roles to Compare Against (pick 2 or more)</Label>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                {roles?.map((r: any) => (
                  <button
                    key={r.id}
                    onClick={() => toggleCompareRole(r.id)}
                    type="button"
                    aria-pressed={compareRoles.includes(r.id)}
                    className={`p-3 border rounded-md cursor-pointer text-left text-sm transition-colors ${
                      compareRoles.includes(r.id)
                        ? "border-primary bg-primary/5 font-medium"
                        : "hover:border-muted-foreground"
                    }`}
                  >
                    {r.title}
                  </button>
                ))}
              </div>
            </div>

            <Button
              onClick={handleCompare}
              disabled={loading || !selectedResume || compareRoles.length < 2}
              type="button"
            >
              {loading && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              Compare Across {compareRoles.length} Role{compareRoles.length !== 1 ? "s" : ""}
            </Button>
          </CardContent>
        </Card>

        {results.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Comparison Matrix</CardTitle>
              {bestRole && (
                <div className="flex items-center gap-2 text-sm text-green-600 mt-1">
                  <Star className="h-4 w-4 fill-current" />
                  Best fit: <strong>{bestRole.role_title}</strong> ({Number(bestRole.overall_score).toFixed(1)}/10)
                </div>
              )}
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr>
                      <th className="text-left py-2 pr-4 font-medium text-muted-foreground w-40">Dimension</th>
                      {results.map((r: any) => (
                        <th key={r.role_id} className="text-center py-2 px-3 font-medium">
                          {r.role_title}
                          {bestRole?.role_id === r.role_id && <Star className="h-3 w-3 inline ml-1 text-amber-500 fill-current" />}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {dimensions.map((dim: string) => (
                      <tr key={dim} className="border-t">
                        <td className="py-2 pr-4 text-muted-foreground">{dim}</td>
                        {results.map((r: any) => {
                          const d = r.dimensional_scores?.find((ds: any) => ds.dimension === dim);
                          const score = d?.score ?? 0;
                          const color = score >= 7 ? "text-green-600" : score >= 5 ? "text-amber-600" : "text-red-600";
                          return (
                            <td key={r.role_id} className={`py-2 px-3 text-center font-semibold ${color}`}>
                              {score.toFixed(1)}
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                    <tr className="border-t-2 border-primary/20">
                      <td className="py-3 pr-4 font-bold">Overall Fit</td>
                      {results.map((r: any) => {
                        const score = Number(r.overall_score);
                        const color = score >= 7 ? "text-green-600" : score >= 5 ? "text-amber-600" : "text-red-600";
                        return (
                          <td key={r.role_id} className={`py-3 px-3 text-center font-bold text-lg ${color}`}>
                            {score.toFixed(1)}
                          </td>
                        );
                      })}
                    </tr>
                    <tr className="border-t">
                      <td className="py-2 pr-4 text-muted-foreground">Recommendation</td>
                      {results.map((r: any) => (
                        <td key={r.role_id} className={`py-2 px-3 text-center text-xs font-medium ${recommendationColors[r.recommendation] || ""}`}>
                          {r.recommendation?.replace(/_/g, " ")}
                        </td>
                      ))}
                    </tr>
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
