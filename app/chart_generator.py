import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import io

class ChartGenerator:
    """Chart generation class for spending summaries"""

    def __init__(self):
        # Modern, vibrant color palette with better contrast
        self.colors = [
            '#FF6B6B',  # Coral Red
            '#4ECDC4',  # Turquoise
            '#95E1D3',  # Mint
            '#FFD93D',  # Yellow
            '#A8E6CF',  # Light Green
            '#FFB6C1',  # Light Pink
            '#87CEEB',  # Sky Blue
            '#DDA0DD',  # Plum
            '#F4A460',  # Sandy Brown
            '#98D8C8'   # Pearl Aqua
        ]

    def create_spending_chart(self, categories: list, amounts: list, currency: str, period_title: str):
        """Create a modern donut chart for spending summary"""
        # Use default style with white background
        plt.style.use('default')

        # Create figure with better proportions
        fig, ax = plt.subplots(figsize=(12, 8))
        fig.patch.set_facecolor('#F8F9FA')  # Light gray background
        ax.set_facecolor('#F8F9FA')

        # Custom autopct function to show percentage only
        def make_autopct(values):
            def my_autopct(pct):
                return f'{pct:.1f}%' if pct > 5 else ''  # Hide labels for small slices
            return my_autopct

        # Create donut chart (pie with hole in center)
        wedges, texts, autotexts = ax.pie(
            amounts,
            labels=None,  # We'll use a legend instead
            autopct=make_autopct(amounts),
            startangle=90,
            colors=self.colors[:len(amounts)],
            textprops={'fontsize': 13, 'color': 'white', 'weight': 'bold'},
            wedgeprops={'edgecolor': 'white', 'linewidth': 3, 'antialiased': True},
            pctdistance=0.75
        )

        # Make it a donut by adding white circle in center
        centre_circle = plt.Circle((0, 0), 0.55, fc='#F8F9FA', linewidth=0)
        ax.add_artist(centre_circle)

        # Add total in the center
        total = sum(amounts)
        ax.text(0, 0.05, f'{total:.0f}', ha='center', va='center',
                fontsize=32, fontweight='bold', color='#2C3E50')
        ax.text(0, -0.15, currency, ha='center', va='center',
                fontsize=16, fontweight='normal', color='#7F8C8D')
        ax.text(0, -0.30, 'Total Spent', ha='center', va='center',
                fontsize=12, fontweight='normal', color='#95A5A6')

        # Style autopct text
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(12)
            autotext.set_weight('bold')

        # Add title at the top
        ax.text(0, 1.35, f'Spending Summary',
                ha='center', va='center',
                fontsize=24, fontweight='bold', color='#2C3E50',
                transform=ax.transData)
        ax.text(0, 1.20, period_title,
                ha='center', va='center',
                fontsize=16, fontweight='normal', color='#7F8C8D',
                transform=ax.transData)

        # Create legend with category names and amounts
        legend_labels = [f'{cat}: {amt:.0f} {currency}' for cat, amt in zip(categories, amounts)]
        legend = ax.legend(
            wedges,
            legend_labels,
            title="Categories",
            loc="center left",
            bbox_to_anchor=(1, 0, 0.5, 1),
            fontsize=15,
            title_fontsize=18,
            frameon=True,
            facecolor='white',
            edgecolor='#E0E0E0',
            framealpha=0.95
        )
        legend.get_title().set_fontweight('bold')
        legend.get_title().set_color('#2C3E50')

        # Equal aspect ratio ensures circular pie
        ax.axis('equal')

        # Adjust layout to prevent legend cutoff
        plt.tight_layout()

        # Save the chart to a bytes buffer with high quality
        buf = io.BytesIO()
        plt.savefig(
            buf,
            format='png',
            bbox_inches='tight',
            dpi=150,
            facecolor='#F8F9FA',
            edgecolor='none',
            pad_inches=0.5
        )
        buf.seek(0)
        plt.close()

        return buf 