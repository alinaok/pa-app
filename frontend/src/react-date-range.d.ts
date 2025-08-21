declare module 'react-date-range' {
  import * as React from 'react';

  export interface Range {
    startDate?: Date;
    endDate?: Date;
    key?: string;
    color?: string;
    autoFocus?: boolean;
    disabled?: boolean;
    showDateDisplay?: boolean;
  }

  export interface DateRangeProps {
    ranges: Range[];
    onChange: (item: { selection: Range }) => void;
    moveRangeOnFirstSelection?: boolean;
    editableDateInputs?: boolean;
    // ...add other props as needed
  }

  export class DateRange extends React.Component<DateRangeProps> {}
}