"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Header } from "@/components/layout/Header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { JDQualityNotice } from "@/components/roles/JDQualityNotice";
import { Loader2 } from "lucide-react";

export default function NewRolePage() {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [jdText, setJdText] = useState("");
  const [blindMode, setBlindMode] = useState(true);
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [qualityReport, setQualityReport] = useState<any>(null);

  const handleAnalyzeJD = async () => {
    if (!jdText.trim()) {
      toast.error("Please enter a job description first");
      return;
    }
    setAnalyzing(true);
    try {
      const report = await api.analyzeJDPreview(jdText);
      setQualityReport(report);
      toast.success("JD quality analysis complete");
    } catch (e: any) {
      toast.error(e.message);
    } finally {
      setAnalyzing(false);
    }
  };

  const handleCreate = async () => {
    if (!title.trim() || !jdText.trim()) {
      toast.error("Please fill in both title and job description");
      return;
    }
    setLoading(true);
    try {
      const role = await api.createRole({ title, jd_text: jdText, blind_mode: blindMode });
      toast.success("Role created successfully");
      router.push(`/roles/${role.id}`);
    } catch (e: any) {
      toast.error(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <Header title="Create New Role" subtitle="Set up a role and paste the job description" />
      <div className="p-6 max-w-3xl">
        <Card>
          <CardHeader>
            <CardTitle>Role Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="title">Role Title</Label>
              <Input
                id="title"
                placeholder="e.g., Senior Backend Engineer"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="jd">Job Description</Label>
              <Textarea
                id="jd"
                placeholder="Paste the full job description here..."
                value={jdText}
                onChange={(e) => setJdText(e.target.value)}
                rows={12}
                className="font-mono text-sm"
              />
            </div>

            <div className="flex items-center gap-3">
              <Switch checked={blindMode} onCheckedChange={setBlindMode} id="blind" />
              <Label htmlFor="blind" className="cursor-pointer">
                Blind Mode — Hide candidate names during AI scoring to reduce bias
              </Label>
            </div>

            {qualityReport && (
              <>
                <JDQualityNotice report={qualityReport} />
                <p className="text-xs text-muted-foreground mt-2">
                  Edit the job description above to address the flagged items, then click "Analyze JD Quality" again.
                </p>
              </>
            )}

            <div className="flex gap-3 pt-4">
              <Button onClick={handleCreate} disabled={loading || !title.trim() || !jdText.trim()}>
                {loading && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                Create Role
              </Button>
              <Button variant="outline" onClick={handleAnalyzeJD} disabled={analyzing || !jdText.trim()}>
                {analyzing && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                Analyze JD Quality
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
