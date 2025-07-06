import { ReactNode } from 'react';

declare module './providers' {
  const Providers: React.FC<{ children: ReactNode }>;
  export { Providers };
  export default Providers;
}
