"use client";

import { useParams, useRouter } from "next/navigation";
import useSWR from "swr";
import { fetcher, api } from "@/lib/api";
import { Header } from "@/components/layout/Header";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";
import { useEffect, useState } from "react";
import { Plus, Trash2, Loader2, RefreshCw } from "lucide-react";
import { JDQualityNotice } from "@/components/roles/JDQualityNotice";

export default function RoleSettingsPage() {
  const params = useParams();
  const roleId = params.id as string;
  const router = useRouter();
  const { data: role, mutate, error: roleError } = useSWR<any>(`/api/roles/${roleId}`, fetcher);
  const [saving, setSaving] = useState(false);
  const [reparsing, setReparsing] = useState(false);
  const [newField, setNewField] = useState({ label: "", description: "", type: "text" });
  const [showAddForm, setShowAddForm] = useState(false);

  const [jdDraft, setJdDraft] = useState("");
  const [jdInitialized, setJdInitialized] = useState(false);
  const [jdAnalyzing, setJdAnalyzing] = useState(false);

  useEffect(() => {
    if (!jdInitialized && role?.jd_text != null) {
      setJdDraft(role.jd_text);
      setJdInitialized(true);
    }
  }, [jdInitialized, role?.jd_text]);

  if (roleError) {
    return (
      <div className="p-6 max-w-3xl mx-auto">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-sm font-medium text-red-800">Failed to load settings.</p>
          <p className="text-xs text-red-600 mt-1">{roleError.message}</p>
          <div className="mt-3">
            <Button onClick={() => mutate()} type="button">
              Retry
            </Button>
          </div>
        </div>
      </div>
    );
  }

  if (!role)
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    );

  const config: any[] = role.extraction_config || [];

  const toggleField = async (fieldName: string) => {
    const updated = config.map((f: any) =>
      f.field === fieldName ? { ...f, enabled: !f.enabled } : f
    );
    await saveConfig(updated);
  };

  const removeField = async (fieldName: string) => {
    const updated = config.filter((f: any) => f.field !== fieldName);
    await saveConfig(updated);
  };

  const addField = async () => {
    if (!newField.label.trim()) { toast.error("Label is required"); return; }
    const fieldKey = newField.label.toLowerCase().replace(/\s+/g, "_").replace(/[^a-z0-9_]/g, "");
    if (config.find((f: any) => f.field === fieldKey)) { toast.error("Field already exists"); return; }
    const updated = [...config, { field: fieldKey, label: newField.label, type: newField.type, enabled: true, description: newField.description }];
    await saveConfig(updated);
    setNewField({ label: "", description: "", type: "text" });
    setShowAddForm(false);
  };

  const saveConfig = async (updatedConfig: any[]) => {
    setSaving(true);
    try {
      await api.updateConfig(roleId, { extraction_config: updatedConfig });
      await mutate();
      toast.success("Config saved");
    } catch (e: any) { toast.error(e.message); }
    finally { setSaving(false); }
  };

  const toggleBlindMode = async () => {
    try {
      await api.updateRole(roleId, { blind_mode: !role.blind_mode });
      await mutate();
      toast.success(`Blind mode ${!role.blind_mode ? "enabled" : "disabled"}`);
    } catch (e: any) { toast.error(e.message); }
  };

  const handleReparse = async () => {
    if (!confirm("Re-extract all resumes with the updated config? This may take a few minutes.")) return;
    setReparsing(true);
    try {
      await api.batchReparse(roleId);
      toast.success("Re-parsing started. Resumes will update shortly.");
    } catch (e: any) { toast.error(e.message); }
    finally { setReparsing(false); }
  };

  const handleSaveAndAnalyzeJD = async () => {
    if (!jdDraft.trim()) {
      toast.error("Job description cannot be empty");
      return;
    }
    setJdAnalyzing(true);
    try {
      await api.updateRole(roleId, { jd_text: jdDraft });
      await api.analyzeJD(roleId);
      await mutate();
      toast.success("JD analysis complete");
    } catch (e: any) {
      toast.error(e.message);
    } finally {
      setJdAnalyzing(false);
    }
  };

  const handleDeleteRole = async () => {
    if (!confirm("Delete this role and all associated resumes/scores? This cannot be undone.")) return;
    try {
      await api.deleteRole(roleId);
      toast.success("Role deleted");
      router.push("/");
    } catch (e: any) {
      toast.error(e.message);
    }
  };

  return (
    <div>
      <Header title={`${role.title} — Settings`} subtitle="Configure extraction fields and scoring options" />
      <div className="p-6 max-w-3xl space-y-6">

        {/* JD Editor */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Job Description (JD)</CardTitle>
            <CardDescription>Edit the JD and run quality analysis.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <Textarea
              value={jdDraft}
              onChange={(e) => setJdDraft(e.target.value)}
              rows={10}
              className="font-mono text-sm"
            />

            <div className="flex flex-wrap items-center gap-3 pt-2">
              <Button
                onClick={handleSaveAndAnalyzeJD}
                disabled={jdAnalyzing || !jdDraft.trim()}
                type="button"
              >
                {jdAnalyzing ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : null}
                {role?.jd_quality_report ? "Save & Re-run JD Quality" : "Save & Analyze JD Quality"}
              </Button>
              <p className="text-xs text-muted-foreground">
                Tip: edit the JD above to address "Vague Requirements", then run analysis again.
              </p>
            </div>

            {role.jd_quality_report ? <JDQualityNotice report={role.jd_quality_report} /> : null}
          </CardContent>
        </Card>

        {/* Blind Mode */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Blind Mode</CardTitle>
            <CardDescription>Hide candidate name, email, and phone from the AI during scoring to reduce bias</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-3">
              <Switch checked={role.blind_mode} onCheckedChange={toggleBlindMode} id="blind" />
              <Label htmlFor="blind">{role.blind_mode ? "PII hidden during scoring (name, email, phone stripped)" : "Names visible during scoring"}</Label>
            </div>
          </CardContent>
        </Card>

        {/* Danger Zone */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Danger Zone</CardTitle>
            <CardDescription>Delete the role and all associated data.</CardDescription>
          </CardHeader>
          <CardContent>
            <Button variant="destructive" onClick={handleDeleteRole} disabled={jdAnalyzing} type="button">
              Delete Role
            </Button>
          </CardContent>
        </Card>

        {/* Extraction Config */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-base">Extraction Parameters</CardTitle>
                <CardDescription className="mt-1">Fields the AI extracts from each resume</CardDescription>
              </div>
              <Badge variant="secondary">v{role.extraction_config_version}</Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              {config.map((field: any) => (
                <div key={field.field} className="flex items-center gap-3 p-3 bg-muted rounded-md">
                  <Switch
                    checked={field.enabled}
                    onCheckedChange={() => toggleField(field.field)}
                    disabled={saving}
                  />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium">{field.label}</p>
                    {field.description && <p className="text-xs text-muted-foreground">{field.description}</p>}
                  </div>
                  <Badge variant="outline" className="text-xs shrink-0">{field.type}</Badge>
                  {!["full_name", "email", "skills", "total_experience_years"].includes(field.field) && (
                    <Button variant="ghost" size="sm" onClick={() => removeField(field.field)} className="text-muted-foreground hover:text-destructive">
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              ))}
            </div>

            {showAddForm ? (
              <div className="border rounded-md p-4 space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <Label>Field Label</Label>
                    <Input placeholder="e.g., Management Experience" value={newField.label} onChange={e => setNewField(p => ({ ...p, label: e.target.value }))} />
                  </div>
                  <div className="space-y-1">
                    <Label>Type</Label>
                    <select className="w-full border rounded-md px-3 py-2 text-sm" value={newField.type} onChange={e => setNewField(p => ({ ...p, type: e.target.value }))}>
                      <option value="text">Text</option>
                      <option value="number">Number</option>
                      <option value="list">List</option>
                    </select>
                  </div>
                </div>
                <div className="space-y-1">
                  <Label>Description (what AI should look for)</Label>
                  <Input placeholder="e.g., Years of team management experience" value={newField.description} onChange={e => setNewField(p => ({ ...p, description: e.target.value }))} />
                </div>
                <div className="flex gap-2">
                  <Button size="sm" onClick={addField} disabled={saving}>Add Field</Button>
                  <Button size="sm" variant="ghost" onClick={() => setShowAddForm(false)}>Cancel</Button>
                </div>
              </div>
            ) : (
              <Button variant="outline" size="sm" onClick={() => setShowAddForm(true)}>
                <Plus className="h-4 w-4 mr-2" /> Add Custom Field
              </Button>
            )}

            <div className="pt-2">
              <Button variant="outline" onClick={handleReparse} disabled={reparsing}>
                {reparsing ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <RefreshCw className="h-4 w-4 mr-2" />}
                Re-parse All Resumes with New Config
              </Button>
              <p className="text-xs text-muted-foreground mt-1">
                This re-extracts all resumes using the current field configuration.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
