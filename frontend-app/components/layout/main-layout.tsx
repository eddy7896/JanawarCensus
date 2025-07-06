import { ReactNode } from "react"
import { SiteHeader } from "./site-header"

type MainLayoutProps = {
  children: ReactNode
}

export function MainLayout({ children }: MainLayoutProps) {
  return (
    <div className="min-h-screen bg-background flex flex-col">
      <SiteHeader />
      <main className="flex-1">
        <div className="container px-6 py-10 mx-auto max-w-7xl">
          <div className="px-4 py-6">
            {children}
          </div>
        </div>
      </main>
    </div>
  )
}
