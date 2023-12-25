export type Sample = {
  input: string;
  output: string;
};

export type ProblemData = {
  id: number;
  url: string;
  source: {
    sourceString: string;
    year: number;
    contest: string;
    division: string;
  };
  submittable: boolean;
  title: {
    titleString: string;
    place: number;
    name: string;
  };
  input: string;
  output: string;
  samples: Sample[];
};
