import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Menu } from "lucide-react"
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"
import { NavigationMenu, NavigationMenuItem, NavigationMenuLink, NavigationMenuList, navigationMenuTriggerStyle } from "@/components/ui/navigation-menu"
import { ThemeToggle } from "@/components/theme-toggle"

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="relative h-16">
        {/* Logo - Positioned 20 units from the left */}
        <div className="absolute left-20 top-1/2 -translate-y-1/2">
          <Link href="/" className="flex items-center space-x-2">
            <span className="font-bold text-lg">Janawar Census</span>
          </Link>
        </div>
        
        {/* Centered Navigation */}
        <nav className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2">
          <NavigationMenu>
            <NavigationMenuList className="gap-2">
              <NavigationMenuItem>
                <NavigationMenuLink asChild>
                  <Link href="/dashboard" className={navigationMenuTriggerStyle()}>
                    Dashboard
                  </Link>
                </NavigationMenuLink>
              </NavigationMenuItem>
              <NavigationMenuItem>
                <NavigationMenuLink asChild>
                  <Link href="/animals" className={navigationMenuTriggerStyle()}>
                    Animals
                  </Link>
                </NavigationMenuLink>
              </NavigationMenuItem>
              <NavigationMenuItem>
                <NavigationMenuLink asChild>
                  <Link href="/reports" className={navigationMenuTriggerStyle()}>
                    Reports
                  </Link>
                </NavigationMenuLink>
              </NavigationMenuItem>
            </NavigationMenuList>
          </NavigationMenu>
        </nav>
        
        {/* Theme Toggle - Right side */}
        <div className="absolute right-6 top-1/2 -translate-y-1/2 flex items-center space-x-2">
          <ThemeToggle />
          
          {/* Mobile menu button */}
          <div className="md:hidden">
            <Sheet>
              <SheetTrigger asChild>
                <Button variant="ghost" size="icon">
                  <Menu className="h-5 w-5" />
                  <span className="sr-only">Toggle Menu</span>
                </Button>
              </SheetTrigger>
              <SheetContent side="left">
                <nav className="grid gap-4 py-6">
                  <Link href="/dashboard" className="text-lg font-semibold hover:underline">
                    Dashboard
                  </Link>
                  <Link href="/animals" className="text-muted-foreground hover:text-foreground hover:underline">
                    Animals
                  </Link>
                  <Link href="/reports" className="text-muted-foreground hover:text-foreground hover:underline">
                    Reports
                  </Link>
                </nav>
              </SheetContent>
            </Sheet>
          </div>
        </div>
      </div>
    </header>
  );
}
