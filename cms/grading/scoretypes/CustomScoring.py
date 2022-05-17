#!/usr/bin/env python3

# Contest Management System - http://cms-dev.github.io/
# Copyright © 2010-2012 Giovanni Mascellani <mascellani@poisson.phc.unipi.it>
# Copyright © 2010-2018 Stefano Maggiolo <s.maggiolo@gmail.com>
# Copyright © 2010-2012 Matteo Boscariol <boscarim@hotmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from . import ScoreTypeGroup


# Dummy function to mark translatable string.
def N_(message):
    return message


class CustomScoring(ScoreTypeGroup):
    """The score of a submission is the sum of the product of the
    minimum of the ranges with the multiplier of that range.
    Parameters are [[m, t], ... ] (see ScoreTypeGroup).
    """

    def compute_score(self, submission_result):
        """See ScoreType.compute_score."""
        # Actually, this means it didn't even compile!
        if not submission_result.evaluated():
            return 0.0, [], 0.0, [], ["%lg" % 0.0 for _ in self.parameters]

        score = 0
        subtasks = []
        public_score = 0
        public_subtasks = []
        ranking_details = []

        targets = self.retrieve_target_testcases()
        evaluations = {ev.codename: ev for ev in submission_result.evaluations}

        for st_idx, parameter in enumerate(self.parameters):
            target = targets[st_idx]

            testcases = []
            public_testcases = []
            previous_tc_all_correct = True
            for tc_idx in target:
                tc_outcome = self.get_public_outcome(
                    float(evaluations[tc_idx].outcome), parameter)

                testcases.append({
                    "idx": tc_idx,
                    "outcome": tc_outcome,
                    "text": evaluations[tc_idx].text,
                    "time": evaluations[tc_idx].execution_time,
                    "memory": evaluations[tc_idx].execution_memory,
                    "show_in_restricted_feedback": previous_tc_all_correct})
                if self.public_testcases[tc_idx]:
                    public_testcases.append(testcases[-1])
                    # Only block restricted feedback if this is the first
                    # *public* non-correct testcase, otherwise we might be
                    # leaking info on private testcases.
                    if tc_outcome != "Correct":
                        previous_tc_all_correct = False
                else:
                    public_testcases.append({"idx": tc_idx})

            st_score_fraction = self.reduce(
                [float(evaluations[tc_idx].outcome) for tc_idx in target],
                parameter)
            st_score = st_score_fraction * parameter[0]
            isOk = st_score_fraction >= 1.0
            if isOk:
                for sub in parameter[2]:
                    if subtasks[sub]['score_fraction'] <= 0.0:
                        subtasks[sub]['score_fraction'] = 1.0
                        public_subtasks[sub]['score_fraction']=1.0
                        score+=subtasks[sub]['max_score']
                        public_score+=subtasks[sub]['max_score']
                        ranking_details[sub]="%g" % round(subtasks[sub]['max_score'],2) 

            score += st_score
            subtasks.append({
                "idx": st_idx + 1,
                # We store the fraction so that an "example" testcase
                # with a max score of zero is still properly rendered as
                # correct or incorrect.
                "score_fraction": st_score_fraction,
                "max_score": parameter[0],
                "testcases": testcases})
            if all(self.public_testcases[tc_idx] for tc_idx in target):
                public_score += st_score
                public_subtasks.append(subtasks[-1])
            else:
                public_subtasks.append({"idx": st_idx + 1,
                                        "testcases": public_testcases})
            ranking_details.append("%g" % round(st_score, 2))

        return score, subtasks, public_score, public_subtasks, ranking_details

    def get_public_outcome(self, outcome, unused_parameter):
        """See ScoreTypeGroup."""
        if outcome <= 0.0:
            return N_("Not correct")
        elif outcome >= 1.0:
            return N_("Correct")
        else:
            return N_("Partially correct")

    def reduce(self, outcomes, unused_parameter):
        """See ScoreTypeGroup."""
        return min(outcomes)
