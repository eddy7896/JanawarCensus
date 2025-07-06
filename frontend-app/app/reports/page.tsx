"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Download, FileText, BarChart2, Activity, Calendar } from "lucide-react";
import Link from "next/link";

const reportTypes = [
  {
    id: 'population',
    title: 'Population Overview',
    description: 'Detailed report on current animal populations by species and location',
    icon: <BarChart2 className="h-6 w-6 text-primary" />,
  },
  {
    id: 'health',
    title: 'Health Status',
    description: 'Summary of animal health conditions and medical history',
    icon: <Activity className="h-6 w-6 text-primary" />,
  },
  {
    id: 'movement',
    title: 'Movement Patterns',
    description: 'Analysis of animal movements and migration patterns',
    icon: <Activity className="h-6 w-6 text-primary" />,
  },
  {
    id: 'conservation',
    title: 'Conservation Status',
    description: 'Report on conservation efforts and endangered species',
    icon: <Activity className="h-6 w-6 text-primary" />,
  },
];

export default function ReportsPage() {
  return (
    <div className="space-y-10">
      <div className="space-y-10">
        <h1 className="text-3xl font-bold tracking-tight">Reports</h1>
        <p className="text-muted-foreground">
          Generate and view detailed reports on wildlife data
        </p>
      </div>

      <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-4">
        {reportTypes.map((report) => (
          <Card key={report.id} className="hover:shadow-md transition-shadow p-1">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
              <CardTitle className="text-sm font-medium">
                {report.title}
              </CardTitle>
              {report.icon}
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground mb-4">{report.description}</p>
              <div className="flex space-x-3">
                <Button variant="outline" size="sm" asChild className="flex-1">
                  <Link href={`/reports/${report.id}`} className="text-center">
                    View
                  </Link>
                </Button>
                <Button variant="ghost" size="sm" className="text-muted-foreground">
                  <Download className="h-4 w-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card className="p-6">
        <CardHeader className="px-0 pt-0">
          <CardTitle>Generate Custom Report</CardTitle>
          <CardDescription>
            Create a custom report with specific parameters
          </CardDescription>
        </CardHeader>
        <CardContent className="px-0">
          <div className="grid gap-6 md:grid-cols-3">
            <div className="space-y-3">
              <label className="text-sm font-medium block">Report Type</label>
              <select className="w-full p-3 border rounded-lg bg-background">
                <option>Select a report type</option>
                {reportTypes.map((report) => (
                  <option key={report.id} value={report.id}>
                    {report.title}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-3">
              <label className="text-sm font-medium block">Date Range</label>
              <select className="w-full p-3 border rounded-lg bg-background">
                <option value="7">Last 7 days</option>
                <option value="30">Last 30 days</option>
                <option value="90">Last 90 days</option>
              </select>
            </div>
            <div className="flex items-end">
              <Button className="w-full h-11">
                <FileText className="h-4 w-4 mr-2" />
                Generate Report
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
