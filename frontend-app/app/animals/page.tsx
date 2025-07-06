"use client";

import { DataTable } from "@/components/ui/data-table";
import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";
import Link from "next/link";
import { ColumnDef } from "@tanstack/react-table";

type Animal = {
  id: number;
  species: string;
  name: string;
  location: string;
  lastSeen: string;
};

// Mock data - replace with actual API call
const data: Animal[] = [
  {
    id: 1,
    species: 'Bengal Tiger',
    name: 'Raja',
    location: 'Bandipur National Park',
    lastSeen: '2023-06-15',
  },
  {
    id: 2,
    species: 'Indian Elephant',
    name: 'Gajendra',
    location: 'Kaziranga National Park',
    lastSeen: '2023-06-18',
  },
  {
    id: 3,
    species: 'Indian Leopard',
    name: 'Veera',
    location: 'Gir Forest',
    lastSeen: '2023-06-12',
  },
  {
    id: 4,
    species: 'Asiatic Lion',
    name: 'Simba',
    location: 'Gir National Park',
    lastSeen: '2023-06-20',
  },
];

const columns: ColumnDef<Animal>[] = [
  {
    accessorKey: 'species',
    header: 'Species',
  },
  {
    accessorKey: 'name',
    header: 'Name',
  },
  {
    accessorKey: 'location',
    header: 'Location',
  },

  {
    accessorKey: 'lastSeen',
    header: 'Last Seen',
  },
  {
    id: 'actions',
    cell: ({ row }) => (
      <Button variant="ghost" size="sm" asChild>
        <Link href={`/animals/${row.original.id}`}>View Details</Link>
      </Button>
    ),
  },
];

export default function AnimalsPage() {
  return (
    <div className="space-y-8">
      <div className="space-y-3">
        <h1 className="text-3xl font-bold tracking-tight">Animal Records</h1>
        <p className="text-muted-foreground">
          Manage and track wildlife in your conservation area
        </p>
      </div>
      
      <div className="flex justify-end pb-4">
        <Button asChild>
          <Link href="/animals/new" className="flex items-center gap-2">
            <Plus className="h-4 w-4" />
            Add New Animal
          </Link>
        </Button>
      </div>
      
      <div className="rounded-lg border bg-card p-6">
        <DataTable
          columns={columns}
          data={data}
          enableRowSelection={true}
          onRowSelectionChange={(selectedIds) => {
            console.log('Selected rows:', selectedIds);
          }}
        />
      </div>
    </div>
  );
}
