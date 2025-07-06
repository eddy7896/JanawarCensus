import { ColumnDef } from "@tanstack/react-table"
import { Button } from "@/components/ui/button"
import { ArrowUpDown, MoreHorizontal } from "lucide-react"

export type Animal = {
  id: number
  species: string
  location: string
  status: "Healthy" | "Injured" | "Missing"
  lastSeen: string
}

export const columns: ColumnDef<Animal>[] = [
  {
    accessorKey: "species",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          className="p-0 hover:bg-transparent"
        >
          Species
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      )
    },
  },
  {
    accessorKey: "location",
    header: "Location",
  },
  {
    accessorKey: "status",
    header: "Status",
    cell: ({ row }) => {
      const status = row.getValue("status") as string
      const statusColors = {
        Healthy: "bg-green-100 text-green-800",
        Injured: "bg-yellow-100 text-yellow-800",
        Missing: "bg-red-100 text-red-800",
      }
      
      return (
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[status as keyof typeof statusColors]}`}>
          {status}
        </span>
      )
    },
  },
  {
    accessorKey: "lastSeen",
    header: "Last Seen",
    cell: ({ row }) => {
      const date = new Date(row.getValue("lastSeen"))
      return date.toLocaleDateString()
    },
  },
  {
    id: "actions",
    cell: () => (
      <Button variant="ghost" size="sm">
        <MoreHorizontal className="h-4 w-4" />
        <span className="sr-only">View details</span>
      </Button>
    ),
  },
]
