"use client"

import { useState, useCallback, useMemo } from "react"
import { format, subMonths, isWithinInterval, parseISO } from "date-fns"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { DataCard } from "@/components/ui/data-card"
import { DataTable } from "@/components/ui/data-table"
import { DateRange } from "react-day-picker"
import { DateRangePicker } from "@/components/date-range-picker"
import { Button } from "@/components/ui/button"
import { Download } from "lucide-react"
import { ColumnDef, Row } from "@tanstack/react-table"

type Animal = {
  id: number
  species: string
  location: string
  status: "Healthy" | "Injured" | "Missing"
  lastSeen: string
}

// Define the columns for the data table
const columns: ColumnDef<Animal>[] = [
  {
    accessorKey: "species",
    header: "Species",
  },
  {
    accessorKey: "location",
    header: "Location",
  },

  {
    accessorKey: "lastSeen",
    header: "Last Seen",
    cell: ({ row }) => {
      const date = new Date(row.getValue("lastSeen"))
      return date.toLocaleDateString()
    },
  },
]

// Sample data for the dashboard
const stats = [
  { title: "Total Animals", value: "1,234", description: "Across all regions", trend: { value: "12%", isPositive: true } },
  { title: "Species Count", value: "45", description: "Different species recorded", trend: { value: "5%", isPositive: true } },
  { title: "Sightings Today", value: "23", description: "New sightings", trend: { value: "3%", isPositive: false } },
  { title: "Active Rangers", value: "17", description: "On duty", trend: { value: "2%", isPositive: true } },
]

// Sample data for the chart
const chartData = [
  { name: 'Jan', tigers: 40, leopards: 24, elephants: 32 },
  { name: 'Feb', tigers: 30, leopards: 13, elephants: 28 },
  { name: 'Mar', tigers: 20, leopards: 18, elephants: 35 },
  { name: 'Apr', tigers: 27, leopards: 19, elephants: 30 },
  { name: 'May', tigers: 34, leopards: 22, elephants: 32 },
  { name: 'Jun', tigers: 38, leopards: 26, elephants: 34 },
]

// Sample data for the table
const animals = [
  { id: 1, species: "Bengal Tiger", location: "Zone A", status: "Healthy", lastSeen: "2025-07-05" },
  { id: 2, species: "Indian Leopard", location: "Zone B", status: "Injured", lastSeen: "2025-07-04" },
  { id: 3, species: "Asian Elephant", location: "Zone C", status: "Healthy", lastSeen: "2025-07-06" },
  { id: 4, species: "Indian Rhinoceros", location: "Zone A", status: "Healthy", lastSeen: "2025-07-03" },
  { id: 5, species: "Bengal Tiger", location: "Zone D", status: "Missing", lastSeen: "2025-06-28" },
]

// Sample data generation functions
interface ChartDataPoint {
  name: string
  tigers: number
  leopards: number
  elephants: number
}

function generateChartData(dateRange: { from: Date; to: Date }): ChartDataPoint[] {
  const months: ChartDataPoint[] = []
  let currentDate = new Date(dateRange.from)
  
  while (currentDate <= dateRange.to) {
    const month = format(currentDate, 'MMM')
    const year = format(currentDate, 'yyyy')
    const key = `${month} ${year}`
    
    // Only add the month if it's not already in the array
    if (!months.some(m => m.name === key)) {
      months.push({
        name: key,
        tigers: Math.floor(Math.random() * 50) + 10,
        leopards: Math.floor(Math.random() * 30) + 5,
        elephants: Math.floor(Math.random() * 40) + 15,
      })
    }
    
    // Move to the first day of the next month
    currentDate = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1)
  }
  
  return months
}

function generateTableData() {
  const species = ["Bengal Tiger", "Indian Leopard", "Asian Elephant", "Indian Rhinoceros", "Indian Bison"]
  const statuses = ["Healthy", "Injured", "Missing"]
  const zones = ["Zone A", "Zone B", "Zone C", "Zone D"]
  
  return Array.from({ length: 20 }, (_, i) => ({
    id: i + 1,
    species: species[Math.floor(Math.random() * species.length)],
    location: zones[Math.floor(Math.random() * zones.length)],
    status: statuses[Math.floor(Math.random() * statuses.length)] as "Healthy" | "Injured" | "Missing",
    lastSeen: format(
      new Date().setDate(Math.floor(Math.random() * 30) + 1),
      "yyyy-MM-dd"
    ),
  }))
}

export default function DashboardPage() {
  const [dateRange, setDateRange] = useState<DateRange | undefined>({
    from: subMonths(new Date(), 6),
    to: new Date(),
  })
  
  // Handle date range changes
  const handleDateRangeChange = useCallback((range: DateRange | undefined) => {
    setDateRange(range)
  }, [])
  
  // Generate data based on the selected date range
  const chartData = useMemo(() => 
    dateRange?.from && dateRange?.to 
      ? generateChartData({ from: dateRange.from, to: dateRange.to })
      : [],
    [dateRange]
  )
  
  // Filter table data based on date range
  const filteredTableData = useMemo(() => {
    if (!dateRange?.from || !dateRange?.to) return generateTableData()
    
    return generateTableData().filter(animal => {
      const lastSeen = parseISO(animal.lastSeen)
      return isWithinInterval(lastSeen, {
        start: dateRange.from!,
        end: dateRange.to!
      })
    })
  }, [dateRange])
  
  // Calculate stats based on the filtered data
  const stats = useMemo(() => [
    { 
      title: "Total Animals", 
      value: filteredTableData.length.toLocaleString(),
      description: `Tracked animals`, 
      trend: { value: "12%", isPositive: true } 
    },
    { 
      title: "Species Count", 
      value: new Set(filteredTableData.map(a => a.species)).size.toString(), 
      description: "Different species", 
      trend: { value: "5%", isPositive: true } 
    },
    { 
      title: "Healthy Animals", 
      value: filteredTableData.filter(a => a.status === 'Healthy').length.toString(), 
      description: "In good condition", 
      trend: { value: "3%", isPositive: true } 
    },
    { 
      title: "Active Zones", 
      value: new Set(filteredTableData.map(a => a.location)).size.toString(), 
      description: "Areas with activity", 
      trend: { value: "2%", isPositive: true } 
    }
  ], [filteredTableData])
  
  const [selectedRows, setSelectedRows] = useState<number[]>([])
  
  // Handle row selection change
  const handleRowSelectionChange = useCallback((selectedIds: number[]) => {
    setSelectedRows(selectedIds)
    console.log('Selected rows:', selectedIds)
  }, [])
  
  return (
    <div className="space-y-8">
      <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Wildlife Census</h1>
          <p className="text-muted-foreground">Track and manage wildlife population data</p>
        </div>
        <div className="flex items-center space-x-2">
          <DateRangePicker 
            date={dateRange} 
            setDate={handleDateRangeChange} 
          />
          <Button variant="outline" size="sm" className="ml-auto gap-1">
            <Download className="h-4 w-4" />
            <span className="sr-only sm:not-sr-only">Export</span>
          </Button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat, i) => (
          <DataCard
            key={i}
            title={stat.title}
            value={stat.value}
            description={stat.description}
            trend={stat.trend}
          />
        ))}
      </div>

      {/* Chart */}
      <div className="rounded-lg border p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">Sightings Trend</h2>
          <div className="flex space-x-2
          ">
            <Button variant="outline" size="sm" onClick={() => setDateRange({
              from: subMonths(new Date(), 6),
              to: new Date()
            })}>
              Last 6 Months
            </Button>
            <Button variant="outline" size="sm" onClick={() => setDateRange({
              from: subMonths(new Date(), 12),
              to: new Date()
            })}>
              Last Year
            </Button>
          </div>
        </div>
        <div className="h-[300px]">
          {chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip 
                  content={({ active, payload, label }) => {
                    if (active && payload && payload.length) {
                      return (
                        <div className="rounded-lg border bg-background p-4 shadow-sm">
                          <p className="font-medium">{label}</p>
                          {payload.map((entry, index) => (
                            <p key={`item-${index}`} style={{ color: entry.color }}>
                              {entry.name}: {entry.value}
                            </p>
                          ))}
                        </div>
                      )
                    }
                    return null
                  }}
                />
                <Legend />
                <Bar dataKey="tigers" fill="#8884d8" name="Tigers" />
                <Bar dataKey="leopards" fill="#82ca9d" name="Leopards" />
                <Bar dataKey="elephants" fill="#ffc658" name="Elephants" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex h-full items-center justify-center text-muted-foreground">
              No data available for the selected date range
            </div>
          )}
        </div>
      </div>

      {/* Recent Sightings Table */}
      <div className="rounded-lg border p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">Recent Sightings</h2>
          <div className="flex space-x-2">
            {selectedRows.length > 0 && (
              <Button variant="outline" size="sm" className="text-red-600 hover:bg-red-50">
                Delete Selected ({selectedRows.length})
              </Button>
            )}
            <Button variant="outline" size="sm">
              Export
            </Button>
          </div>
        </div>
        <div className="rounded-md border">
          <DataTable<Animal, unknown>
            columns={columns}
            data={filteredTableData}
            onRowSelectionChange={handleRowSelectionChange}
            enableRowSelection={true}
          />
        </div>
      </div>
    </div>
  )
}
